import os
from google.api_core.exceptions import Unknown
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from google import genai
import json
import re

from ..models import (ProductModel, MyProducts, ProductCategory, ProductLine, ProductBrand, UserProfile, EAN,
                     Questionnaire, Question, Option, Answer, QuestionnaireEntity)
from ..serializers import (ProductReadSerializer, ProductWriteSerializer,
                          ProductCategoryNameSerializer,
                          ProductLineSerializer,
                          BrandSerializer)

import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

import logging
import mimetypes
from .permissions import (
    IsManufacturingUser,
    IsRetailUser,
    IsAuthenticated
)

from pydantic import BaseModel, Field, NonNegativeInt, RootModel
from typing import Annotated

from pydantic.dataclasses import dataclass

@dataclass
class ValueRange:
    lo: float
    hi: float

class Answer(BaseModel):
    option: str
    value: Annotated[float, ValueRange(-1.0, 1.0)]
    context: str | None = Field(default="")
    page: NonNegativeInt  | None = Field(default=-1)

class QuestionAnswers(BaseModel):
    Question: str
    Answers: list[Answer]

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GeminiQuotaExceededError(Exception):
    def __init__(self, retry_after_seconds: int | None = None):
        super().__init__("Gemini quota exhausted")
        self.retry_after_seconds = retry_after_seconds

class ProductView(APIView):
    # GET should be allowed for any authenticated user (viewing a product)
    # POST/PUT (creation/update) remain restricted to manufacturing users.
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        else:
            return [IsManufacturingUser()]

    def post(self, request):
        many = isinstance(request.data, list)
        serializer = ProductWriteSerializer(
            data=request.data, many=many, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        instances = serializer.save()

        # Re‑serialize for output (optional)
        out = ProductReadSerializer(instances, many=many, context={'request': request})
        status_code = status.HTTP_201_CREATED if many else status.HTTP_200_OK
        return Response(out.data, status=status_code)

    def put(self, request, product_id=None):
        obj = get_object_or_404(ProductModel, pk=product_id)
        serializer = ProductWriteSerializer(
            obj, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, product_id):
        obj = get_object_or_404(ProductModel, pk=product_id)
        out = ProductReadSerializer(obj, context={'request': request})
        return Response(out.data)


class BrandView(APIView):
    """
    GET: View brand list or details.
    Requires: Any Authenticated User.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, brand_id=None):
        # Permission handled by DRF
        if brand_id:
            brand = get_object_or_404(ProductBrand, pk=brand_id)
            serializer = BrandSerializer(brand)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            brands = ProductBrand.objects.all()
            serializer = BrandSerializer(brands, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class ProductLineView(APIView):
    """
    GET: View product line list or details.
    Requires: Any Authenticated User.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, product_line_id=None):
        # Permission handled by DRF
        if product_line_id:
            product_line = get_object_or_404(ProductLine, pk=product_line_id)
            serializer = ProductLineSerializer(product_line)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            product_lines = ProductLine.objects.all()
            serializer = ProductLineSerializer(product_lines, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class MyProductsView(APIView):
    """
    Manages the 'My Products' list for the currently authenticated user's company.

    POST: Associates products with the user's company.
          Expects JSON body: {"products": [1, 2, 3]}
    DELETE: Removes product associations from the user's company.
            Expects JSON body: {"products": [1, 2, 3]}
    """
    # Apply permissions directly. DRF handles checking these before view methods run.
    # Ensures user is logged in AND has the required role.
    permission_classes = [IsAuthenticated, IsRetailUser]

    def _get_user_company(self, request):
        """
        Safely retrieves the company associated with the authenticated user.
        Returns (Company instance, None) on success,
        or (None, Response object) on error.
        """
        try:
            user_profile = request.user.profile
            company = user_profile.company
            if company is None:
                logger.warning(f"User {request.user.username} has a profile but no company assigned.")
                return None, Response(
                    {'error': 'User is not associated with a company.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return company, None
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile does not exist for user {request.user.username}.")
            return None, Response(
                {'error': 'User profile not found. Cannot determine company.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AttributeError:
            # Catches if user has no 'profile' or profile has no 'company'
            logger.error(f"AttributeError accessing company for user {request.user.username}.")
            return None, Response(
                {'error': 'Could not determine user company due to incomplete profile setup.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request):
        """
        Adds products specified in the request body to the user's company's
        'My Products' list.
        """
        company, error_response = self._get_user_company(request)
        if error_response:
            return error_response

        product_ids = request.data.get('products', []) # Use 'products' key
        if not isinstance(product_ids, list) or not all(isinstance(pid, int) for pid in product_ids):
             return Response(
                 {'error': "Expected a list of integer product IDs under the 'products' key."},
                 status=status.HTTP_400_BAD_REQUEST
             )
        if not product_ids:
             return Response(
                 {'message': 'No product IDs provided to add.'},
                 status=status.HTTP_400_BAD_REQUEST
             )

        # --- Efficient approach using bulk_create ---

        # 1. Find which requested products actually exist
        valid_products = ProductModel.objects.filter(id__in=product_ids)
        valid_product_ids = set(valid_products.values_list('id', flat=True))
        invalid_ids = set(product_ids) - valid_product_ids # IDs requested but not found

        # 2. Find which valid products are *already* associated with the company
        existing_associations = MyProducts.objects.filter(
            company=company,
            product_id__in=valid_product_ids
        ).values_list('product_id', flat=True)
        existing_association_ids = set(existing_associations)

        # 3. Determine which valid products need a *new* association
        products_to_add_ids = valid_product_ids - existing_association_ids

        # 4. Create the new associations in bulk
        my_products_to_create = [
            MyProducts(company=company, product_id=pid) for pid in products_to_add_ids
        ]

        created_objects = []
        if my_products_to_create:
            try:
                # ignore_conflicts=True prevents errors if a record somehow exists
                # despite our check (e.g., race condition). It's safer.
                created_objects = MyProducts.objects.bulk_create(
                    my_products_to_create,
                    ignore_conflicts=True
                )
                logger.info(f"Bulk associated {len(created_objects)} products for company {company.name}.")
            except Exception as e:
                 logger.error(f"Bulk create failed for company {company.name}: {e}")
                 # Depending on requirements, you might want partial success or full rollback
                 return Response(
                     {'error': 'An error occurred while associating products.'},
                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
                 )

        added_count = len(created_objects)
        response_status = status.HTTP_201_CREATED if added_count > 0 else status.HTTP_200_OK # 200 if nothing new was added

        response_data = {
            'message': f'{added_count} new product associations created.',
            'already_associated': list(existing_association_ids),
            'not_found': list(invalid_ids),
        }

        # Refine status based on outcome
        if invalid_ids and added_count == 0 and not existing_association_ids:
            # Only invalid IDs were provided
             response_status = status.HTTP_404_NOT_FOUND
             response_data['message'] = 'None of the provided product IDs were found.'
        elif invalid_ids:
             # Partial success or only existing/invalid found
             response_status = status.HTTP_207_MULTI_STATUS # Good for mixed results


        return Response(response_data, status=response_status)


    def delete(self, request):
        """
        Removes products specified in the request body from the user's company's
        'My Products' list.
        """
        company, error_response = self._get_user_company(request)
        if error_response:
            return error_response

        product_ids = request.data.get('products', []) # Use 'products' key
        if not isinstance(product_ids, list) or not all(isinstance(pid, int) for pid in product_ids):
             return Response(
                 {'error': "Expected a list of integer product IDs under the 'products' key."},
                 status=status.HTTP_400_BAD_REQUEST
             )
        if not product_ids:
             return Response(
                 {'message': 'No product IDs provided to remove.'},
                 status=status.HTTP_400_BAD_REQUEST
             )

        # Perform deletion efficiently using the ORM's filter().delete()
        deleted_count, _ = MyProducts.objects.filter(
            company=company,
            product_id__in=product_ids # Filter by company and the product IDs provided
        ).delete()

        if deleted_count == 0:
             # This means no associations matched the company AND the provided product IDs.
             # It doesn't necessarily mean the products themselves don't exist.
             logger.warning(f"Attempted to delete product associations for company {company.name}, but none matched IDs: {product_ids}")
             return Response(
                 {'message': 'No matching product associations found for this company and the provided IDs.'},
                 status=status.HTTP_404_NOT_FOUND # 404 is appropriate if nothing was found to delete
             )

        # logger.info(f"Deleted {deleted_count} product associations for company {company.name}.")
        return Response(
            {'message': f'{deleted_count} product associations removed successfully.'},
            status=status.HTTP_200_OK # OK indicates successful deletion
        )


class ProductCategories(APIView):
    """
    GET: View list of all product categories.
    Requires: Any Authenticated User.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Permission handled by DRF
        produductcategories = ProductCategory.objects.all()
        serializer = ProductCategoryNameSerializer(produductcategories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SustainabilityReportView(APIView):
    """
    POST: Upload sustainability report PDF for a specific product.
    Requires: Manufacturing User (product owner).
    """
    permission_classes: list[type[IsAuthenticated] | type[IsManufacturingUser]] = [IsAuthenticated, IsManufacturingUser]

    # Maximum file size in bytes (50MB)
    MAX_FILE_SIZE: int = 50 * 1024 * 1024

    # Get the vertex AI
    GCP_VERTEX_AI_API_KEY = os.environ.get("GCP_VERTEX_AI_API_KEY")

    # Temporary in-memory storage for uploaded PDF files
    uploaded_reports: dict[Unknown, Unknown] = {}

    def post(self, request, product_id):
        """
        Upload one or more sustainability report PDF files for the specified product entity.
        The files are stored in memory temporarily for further processing.
        """
        if self.GCP_VERTEX_AI_API_KEY is None:
            return Response(
                {'error': 'Vertex AI is not configured on the backend.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            from ..models import ProductEntity
            product_entity = ProductEntity.objects.get(pk=product_id)
            product = product_entity.get_subclass_instance()
        except ProductEntity.DoesNotExist:
            return Response(
                {'error': 'Product entity not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle multiple files
        uploaded_files = request.FILES.getlist('files')
        
        # Fallback to single file 'file' if 'files' is empty (backward compatibility)
        if not uploaded_files and 'file' in request.FILES:
             uploaded_files = [request.FILES['file']]

        if not uploaded_files:
            return Response(
                {'error': 'No files provided. Please upload PDF file(s).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deduplicate files based on name and size
        unique_files_map = {}
        for f in uploaded_files:
            key = (f.name, f.size)
            if key not in unique_files_map:
                unique_files_map[key] = f
            else:
                logger.warning(f"Duplicate file detected and skipped: {f.name}")
        
        uploaded_files = list(unique_files_map.values())

        if not uploaded_files:
             return Response(
                {'error': 'No unique files to process.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_gemini_files = []
        
        try:
            # Upload file(s) to Gemini
            client = genai.Client(api_key=self.GCP_VERTEX_AI_API_KEY)
            if client is None:
                logger.error("Gemini client is None")
                return Response(
                    {'error': 'Gemini client is null.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            for uploaded_file in uploaded_files:
                if uploaded_file.size > self.MAX_FILE_SIZE:
                    return Response(
                        {'error': f'File "{uploaded_file.name}" too large. Maximum size allowed is {self.MAX_FILE_SIZE // (1024*1024)}MB.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not self._is_valid_pdf(uploaded_file):
                    return Response(
                        {'error': f'Invalid file type for "{uploaded_file.name}". Please upload a PDF file.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                uploaded_gemini_file = self._upload_to_gemini(client, uploaded_file)
                if uploaded_gemini_file:
                     valid_gemini_files.append(uploaded_gemini_file)
                else: 
                     logger.error(f"Failed to upload file {uploaded_file.name} to Gemini")

            if not valid_gemini_files:
                 return Response(
                    {'error': 'Failed to upload any valid files to Gemini.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


            # Get questionnaire data for this product
            questionnaire_data = self._get_product_questionnaires(product)

            if not questionnaire_data:
                return Response(
                    {'message': 'No questionnaires found for this product to process.'},
                    status=status.HTTP_200_OK
                )

            # Generate AI answers using Gemini with ALL uploaded files
            try:
                ai_responses = self._process_with_gemini(valid_gemini_files, questionnaire_data, client)
            except GeminiQuotaExceededError as exc:
                payload = {
                    'error': 'AI service quota is currently exhausted. Please retry shortly.',
                    'error_code': 'gemini_quota_exhausted',
                    'retry_after_seconds': exc.retry_after_seconds,
                }
                if exc.retry_after_seconds:
                    return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE, headers={'Retry-After': str(exc.retry_after_seconds)})
                return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Process and return the results
            return Response({
                'message': f'Successfully processed {len(ai_responses)} questionnaire responses from {len(valid_gemini_files)} file(s).',
                'responses': ai_responses
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Error processing sustainability report", exc_info=True)
            
            return Response(
                {'error': f'Failed to process report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_product_questionnaires(self, product):
        """Get all questionnaires associated with this product AND related entities in the hierarchy."""
        from ..models import ProductModel, ProductLine, ProductBrand
        questionnaire_data = []

        # Determine which entities to check based on what was passed in
        entities_to_check = []
        if isinstance(product, ProductModel):
            # If ProductModel: check Model + its Line + its Brand
            entities_to_check.append(product)
            if hasattr(product, 'product_line') and product.product_line:
                entities_to_check.append(product.product_line)
                if hasattr(product.product_line, 'brand_fk') and product.product_line.brand_fk:
                    entities_to_check.append(product.product_line.brand_fk)

        elif isinstance(product, ProductLine):
            # If ProductLine: check Line + its Brand + all Models under this Line
            entities_to_check.append(product)
            if hasattr(product, 'brand_fk') and product.brand_fk:
                entities_to_check.append(product.brand_fk)
            # Get all ProductModels under this ProductLine
            models = ProductModel.objects.filter(product_line=product)
            entities_to_check.extend(models)
            logger.info(f"Found {models.count()} ProductModels under ProductLine {product.id}")

        elif isinstance(product, ProductBrand):
            # If ProductBrand: check Brand + all Lines + all Models
            entities_to_check.append(product)
            # Get all ProductLines under this Brand
            lines = ProductLine.objects.filter(brand_fk=product)
            entities_to_check.extend(lines)
            # Get all ProductModels under these Lines
            models = ProductModel.objects.filter(product_line__in=lines)
            entities_to_check.extend(models)
            logger.info(f"Found {lines.count()} ProductLines and {models.count()} ProductModels under Brand {product.id}")

        # Collect questionnaires from all identified entities with entity context
        for entity in entities_to_check:
            entity_questionnaires = QuestionnaireEntity.objects.filter(
                product_entity=entity
            ).select_related('questionnaire__aspect').prefetch_related(
                'questionnaire__question_set__option_set'
            )
            logger.info(f"Found {entity_questionnaires.count()} questionnaires for entity {entity.id} (type: {type(entity).__name__})")

            # Determine entity type and name for context
            entity_type = "product model" if isinstance(entity, ProductModel) else \
                          "product line" if isinstance(entity, ProductLine) else \
                          "brand" if isinstance(entity, ProductBrand) else "product"
            entity_name = str(entity)

            for qe in entity_questionnaires:
                questionnaire = qe.questionnaire
                for question in questionnaire.question_set.all():
                    options_list = [option.option_text for option in question.option_set.all()]
                    questionnaire_data.append({
                        'question': question.question_text,
                        'options': options_list,
                        'question_id': question.id,
                        'option_objects': list(question.option_set.all()),
                        'is_single_choice': question.is_single_choice,
                        'entity_type': entity_type,
                        'entity_name': entity_name,
                        'instructions': question.instructions
                    })

        logger.info(f"Total questions collected from all entities: {len(questionnaire_data)}")
        return questionnaire_data

    def _process_with_gemini(self, uploaded_files, questionnaire_data, client):
        from google.genai.types import Content
        from ..models.utils import to_bibtex, ValidationError as DjangoValidationError

        # Wrapper schema for list of answers (include optional `source`)
        class Answer(BaseModel):
            option_id: int
            # We still keep text for debugging/fallback context if needed, but rely on ID
            option_text: str | None = None 
            value: float
            page: int | None = -1
            source: str | None = ""

        class QuestionResponse(BaseModel):
            question_id: int
            question_text: str | None = None
            answers: list[Answer]

        class QuestionResponseList(RootModel[list[QuestionResponse]]):
            pass

        # Construct prompt with IDs and instructions
        questions_block = "\n".join([
            f"Question ID {q['question_id']}: {q['question']}" + 
            (f"\nInstructions: {q['instructions']}" if q.get('instructions') else "") +
            "\nOptions:\n" + 
            "\n".join([f"- ID {opt_obj.id}: {opt_obj.option_text}" for opt_obj in q['option_objects']])
            for q in questionnaire_data
        ])

        prompt = f"""
        Analyze the sustainability report and answer each question. Use JSON ONLY.

        For each question, provide:
        - option: The selected option name
        - value: Confidence between 0–1; use 0 if evidence not found
        - page: Page number where quote appears (-1 if unknown)
        - source: Valid BibTeX entry (e.g., @article{{...}}, @misc{{title={{...}}, author={{...}}, page={{...}}}}"). Include title, author, year, and a note field with the direct quote from the document. Keep concise. Empty string if no evidence found.

        Key rule: If you answer a question (value > 0), you MUST provide source (BibTeX) with a note field containing the direct quote.
        If no evidence found for a question, use value=0 and leave source="".

        Questions:
        {questions_block}
        """
        
        # Prepare contents list with all files then the prompt
        contents = []
        if isinstance(uploaded_files, list):
            contents.extend(uploaded_files)
        else:
             contents.append(uploaded_files)
        
        contents.append(prompt)

        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": QuestionResponseList,
                }
            )
            # LOGGING: Capture the raw text to see what Gemini actually returned
            logger.info(f"Gemini Raw Response: {response.text[:1000]}...") # Log first 1000 chars to avoid huge logs
        except Exception as exc:
            # Catch network/API/client errors (httpx, httpcore, tenacity, etc.)
            error_message = str(exc)
            error_message_lower = error_message.lower()
            retry_after_seconds = None
            retry_match = re.search(r"Please retry in\s+([0-9.]+)s", error_message)
            if retry_match:
                try:
                    retry_after_seconds = max(1, int(float(retry_match.group(1)) + 0.999))
                except (ValueError, TypeError):
                    retry_after_seconds = None

            if (
                getattr(exc, "status_code", None) == 429
                or "resource_exhausted" in error_message_lower
                or "quota exceeded" in error_message_lower
            ):
                logger.warning("Gemini quota exhausted.")
                raise GeminiQuotaExceededError(retry_after_seconds=retry_after_seconds) from exc

            logger.error("Gemini API call failed", exc_info=True)
            return []

        try:
            parsed = QuestionResponseList.model_validate_json(response.text).root
        except Exception as e:
            logger.error(f"Invalid Gemini JSON Parsing Error: {e}")
            logger.error(f"Failed JSON content: {response.text}")
            return []

        # Map back to DB using IDs
        final = []
        for qa in parsed:
            # Match directly by ID
            match = next((q for q in questionnaire_data if q["question_id"] == qa.question_id), None)
            if not match:
                continue

            processed = []
            for ans in qa.answers:
                # Match Option directly by ID
                option_obj = next((o for o in match["option_objects"] if o.id == ans.option_id), None)
                if option_obj:
                    raw_source = (getattr(ans, 'source', '') or '').strip()
                    # Clean markdown code blocks if present
                    raw_source = re.sub(r'^```\w*\s*', '', raw_source)
                    raw_source = re.sub(r'\s*```$', '', raw_source)
                    raw_source = raw_source.strip()

                    context = (getattr(ans, 'context', '') or '').strip()
                    page = getattr(ans, 'page', -1)
                    final_source = ''

                    is_bibtex = False
                    if raw_source.startswith('@'):
                        try:
                            to_bibtex(raw_source)
                            is_bibtex = True
                        except DjangoValidationError:
                            pass

                    if is_bibtex:
                        # Even for valid BibTeX, add context (quote) as a note field
                        if context:
                            # Insert note field before the closing brace
                            escaped_context = context.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}').replace('"', "''")
                            final_source = raw_source.rstrip() 
                            if final_source.endswith('}'):
                                final_source = final_source[:-1] + f',\n  note = {{{escaped_context}}}\n}}'
                            else:
                                final_source = raw_source  # Fallback if format is unexpected
                        else:
                            final_source = raw_source
                    else:
                        bib_fields = []

                        parsed_json = None
                        if raw_source.startswith('{'):
                            try:
                                parsed_json = json.loads(raw_source)
                            except json.JSONDecodeError:
                                pass

                        if isinstance(parsed_json, dict):
                            for key, value in parsed_json.items():
                                k, v = str(key).lower().strip(), str(value).strip()
                                if k and v:
                                    bib_fields.append((k, v))
                        elif raw_source:
                            bib_fields.append(('note', raw_source))

                        # Add context as a note field (standard BibTeX field)
                        if context:
                            # If there's already a note, combine them
                            existing_notes = [v for k, v in bib_fields if k == 'note']
                            if existing_notes:
                                # Remove existing note fields and re-add combined version
                                bib_fields = [(k, v) for k, v in bib_fields if k != 'note']
                                combined_note = '. '.join(existing_notes + [context])
                                bib_fields.append(('note', combined_note))
                            else:
                                bib_fields.append(('note', context))
                        if page is not None and page > -1:
                            bib_fields.append(('page', str(page)))

                        if bib_fields:
                            field_parts = []
                            for key, value in bib_fields:
                                escaped_value = value.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}').replace('"', "''")
                                field_parts.append(f'  {key} = {{{escaped_value}}}')
                            fields_str = ',\n'.join(field_parts)
                            bibtex_string = f'@misc{{ai_generated,\n{fields_str}\n}}'
                            try:
                                final_source = to_bibtex(bibtex_string)
                            except DjangoValidationError as e:
                                logger.error(f"Failed to generate valid BibTeX from constructed string: {e}")
                                final_source = ''

                    processed.append({
                        "option_id": option_obj.id,
                        "option_text": ans.option_text,
                        "is_true": ans.value >= 0.5,
                        "is_false": ans.value < 0.5,
                        "context": context,
                        "page": page,
                        "confidence": ans.value,
                        "source": final_source
                    })

            final.append({
                "question_id": match["question_id"],
                "question_text": match["question"],
                "answers": processed,
            })
        return final


    def _is_valid_pdf(self, uploaded_file) -> bool:
        """
        Validate that the uploaded file is a PDF.
        Checks both file extension and MIME type.
        """
        # Check file extension
        filename = uploaded_file.name.lower() if uploaded_file.name else ''
        if not filename.endswith('.pdf'):
            return False

        # Check MIME type
        content_type = uploaded_file.content_type
        if content_type not in ['application/pdf']:
            # Also check using mimetypes module as fallback
            guessed_type, _ = mimetypes.guess_type(filename)
            if guessed_type != 'application/pdf':
                return False

        return True
    def _upload_to_gemini(self, client, uploaded_file):
        """
        Uploads a Django UploadedFile (InMemory or Temporary) to Gemini Files API.
        Returns the File object from client.files.upload(...).
        """
        mime = getattr(uploaded_file, "content_type", "application/pdf") or "application/pdf"
        display = getattr(uploaded_file, "name", "report.pdf") or "report.pdf"

        if isinstance(uploaded_file, TemporaryUploadedFile) and hasattr(uploaded_file, "temporary_file_path"):
            return client.files.upload(
                file=uploaded_file.temporary_file_path(),
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp.flush()
            tmp_path = tmp.name

        return client.files.upload(
            file=tmp_path,
        )