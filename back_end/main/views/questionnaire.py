from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Answer, ProductCategory, ProductEntity, QuestionnaireEntity, Query, Question
from ..serializers import AnswerSerializer, SuggestionSerializer, QuestionnaireSerializer, AIAnswerFeedbackSerializer
from django.db import transaction
import logging
from .permissions import (
    IsManufacturingUser,
    IsRetailUser,
    IsAuthenticated,
)
from .permissions import CanAnswerQuestions, can_user_answer_questions
from rest_framework.decorators import api_view, permission_classes
from ..models.products import ProductModel


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Answers(APIView):
    """
    GET: View answers submitted for a specific product entity. (Any Authenticated User)
    POST: Submit new answers for a product entity. (Manufacturing User or Admin)
    PUT: Update an existing answer. (Manufacturing User or Admin)
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method in ['POST', 'PUT']:
            # Only users allowed to answer (manufacturing or admin + company flag) can submit/edit
            permission_classes = [CanAnswerQuestions]
        else:
            permission_classes = [IsAuthenticated] # Default fallback
        return [permission() for permission in permission_classes]

    def get(self, request, product_entity_id):
        # Permission handled by get_permissions
        try:
            # Ensure the entity exists before filtering answers
            ProductEntity.objects.get(id=product_entity_id)
            answers = Answer.objects.filter(product_entity=product_entity_id)
        except ProductEntity.DoesNotExist:
            return Response({'error': f'Product entity with ID {product_entity_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, product_entity_id):
        user = request.user
        if not can_user_answer_questions(user):
            return Response({'error': 'You do not have permission to submit answers.'}, status=status.HTTP_403_FORBIDDEN)

        answers_data = request.data.get('answers', [])
        if not isinstance(answers_data, list):
             return Response({'error': 'Expected a list of answers.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_entity = ProductEntity.objects.get(id=product_entity_id)
        except ProductEntity.DoesNotExist:
            return Response({'error': 'Product entity not found'}, status=status.HTTP_404_NOT_FOUND)

        for answer_datum in answers_data:
            answer_datum['answered_by'] = user.pk
            answer_datum['product_entity'] = product_entity.pk

        serializer = AnswerSerializer(data=answers_data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                 logger.error(f"Error saving answers for entity {product_entity_id}: {str(e)}")
                 return Response({'message': f'Error saving answers: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Invalid answer data submitted for entity {product_entity_id}: {serializer.errors}")
            return Response({'message': 'Invalid answer data provided', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, product_entity_id, answer_id):
        user = request.user
        if not can_user_answer_questions(user):
            return Response({'error': 'You do not have permission to update answers.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            answer = Answer.objects.get(id=answer_id, product_entity=product_entity_id)
        except Answer.DoesNotExist:
            return Response({'error': f'Answer with ID {answer_id} for entity {product_entity_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        if not (user == answer.answered_by or user.profile.role.name == 'Admin'):
           return Response({'error': 'Forbidden: You cannot edit this answer.'}, status=status.HTTP_403_FORBIDDEN)

        update_data = request.data.copy()
        update_data['answered_by'] = user.pk
        update_data['product_entity'] = product_entity_id

        serializer = AnswerSerializer(answer, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': 'Error updating answer', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_entity_questionnaires(request, entity_id):
    try:
        product_category_name = request.query_params.get('product_category')
        entity = ProductEntity.objects.get(id=entity_id)

        questionnaire_entities = QuestionnaireEntity.objects.filter(product_entity=entity)
        questionnaires = [qe.questionnaire for qe in questionnaire_entities]

        # Filter by questionnaire category if product_category is provided
        if hasattr(entity, 'brand') and product_category_name:
            try:
                product_category = ProductCategory.objects.get(name=product_category_name)
                if product_category.questionnaire_category:
                    # Filter questionnaires by the product category's questionnaire category
                    questionnaires = [q for q in questionnaires
                                    if getattr(q, 'questionnaire_category', None) == product_category.questionnaire_category]
            except ProductCategory.DoesNotExist:
                # If category doesn't exist, continue with all questionnaires
                pass

        serializer = QuestionnaireSerializer(questionnaires, many=True)
        return Response(serializer.data)
    except ProductEntity.DoesNotExist:
        return Response(
            {"detail": f"Product entity with ID {entity_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_entity_questionnaires: {str(e)}")
        return Response(
            {"detail": "An error occurred while processing your request."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class Suggestion(APIView):
    """
    POST: Submit a suggestion for an answer edit.
    Requires: Retail User or Admin.
    """
    permission_classes = [IsRetailUser]

    def post(self, request):
        suggestion_data = request.data.get('suggestion', {})
        if not isinstance(suggestion_data, dict):
             return Response({'error': 'Suggestion data must be an object.'}, status=status.HTTP_400_BAD_REQUEST)

        suggestion_data['retail_user'] = request.user.pk

        serializer = SuggestionSerializer(data=suggestion_data)
        if serializer.is_valid():
            try:
                 Answer.objects.get(pk=suggestion_data.get('answer'))
            except Answer.DoesNotExist:
                 return Response({'error': 'The answer you are trying to suggest an edit for does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                 return Response({'error': 'Invalid answer ID provided.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QueryView(APIView):
    """
    GET: Get all unhandled queries/concerns for questions in a product entity (Archr users only).
    POST: Raise a concern (Query) about a question (Non-Archr users).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Only Admin and Manufacturing users who can answer should view unhandled concerns
        if not can_user_answer_questions(user):
            return Response({'error': 'You do not have permission to view concerns.'}, status=status.HTTP_403_FORBIDDEN)

        product_entity_id = request.query_params.get('product_entity')
        if not product_entity_id:
            return Response({'error': 'Product entity ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_entity = ProductEntity.objects.get(id=product_entity_id)
        except ProductEntity.DoesNotExist:
            return Response({'error': 'Product entity not found.'}, status=status.HTTP_404_NOT_FOUND)

        questionnaire_entities = QuestionnaireEntity.objects.filter(product_entity=product_entity)
        questionnaires = [qe.questionnaire for qe in questionnaire_entities]

        # Also include questionnaires linked via the product category, if applicable
        product_category = getattr(product_entity, 'product_category', None) or getattr(product_entity, 'product_line.product_category', None)
        if product_category:
            questionnaires.extend(list(product_category.questionnaires.all()))

        questions = Question.objects.filter(questionnaire__in=questionnaires)

        base_query = Query.objects.filter(question__in=questions, is_handled=False)
        # If the user is not an admin/editor, only show them their own concerns.
        if not can_user_answer_questions(user):
            base_query = base_query.filter(retail_user=user)

        queries = base_query.select_related('retail_user')

        query_data = [{
            'id': q.id,
            'question': q.question.id,
            'suggestion_text': q.suggestion_text,
            'retailUser': q.retail_user.id,
            'retailUserUsername': q.retail_user.username,
            'isHandled': q.is_handled
        } for q in queries]

        return Response(query_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        # Users who can answer should not raise concerns here
        if can_user_answer_questions(user):
            return Response({'error': 'Users with answer editing permissions should submit answers, not concerns.'}, status=status.HTTP_400_BAD_REQUEST)

        suggestion_text = request.data.get('suggestion_text', '')
        question_id = request.data.get('question')
        if not question_id:
            return Response({'error': 'Question ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Prevent duplicate unhandled concerns from the same user for the same question
        existing_query = Query.objects.filter(retail_user=user, question=question, is_handled=False).first()
        if existing_query:
            return Response({'id': existing_query.id, 'message': 'You have already raised a concern for this question.'}, status=status.HTTP_200_OK)

        query = Query.objects.create(
            retail_user=user,
            question=question,
            suggestion_text=suggestion_text,
            is_handled=False
        )

        return Response({'id': query.id, 'message': 'Concern raised successfully.'}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """Retract a concern for the requesting user. Expects `question` in body or query params."""
        user = request.user
        question_id = request.data.get('question') or request.query_params.get('question')
        if not question_id:
            return Response({'error': 'Question ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only allow the retail user who created the concern to retract it and only if it's not handled
        q = Query.objects.filter(retail_user=user, question=question, is_handled=False).first()
        if not q:
            return Response({'error': 'No unhandled concern found for this question by this user.'}, status=status.HTTP_404_NOT_FOUND)

        q.delete()
        return Response({'message': 'Concern retracted.'}, status=status.HTTP_200_OK)

    def patch(self, request, query_id=None):
        """Dismiss/mark a concern as handled. Only users who can answer questions may perform this."""
        user = request.user
        if not can_user_answer_questions(user):
            return Response({'error': 'You do not have permission to dismiss concerns.'}, status=status.HTTP_403_FORBIDDEN)

        if not query_id:
            return Response({'error': 'Query ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            q = Query.objects.get(id=query_id)
        except Query.DoesNotExist:
            return Response({'error': 'Concern not found.'}, status=status.HTTP_404_NOT_FOUND)

        if q.is_handled:
            return Response({'message': 'Concern already handled.'}, status=status.HTTP_200_OK)

        q.is_handled = True
        q.save(update_fields=['is_handled'])
        return Response({'id': q.id, 'message': 'Concern dismissed.'}, status=status.HTTP_200_OK)


class AIAnswerFeedbackView(APIView):
    """Endpoint to receive AI prediction feedback records from the frontend."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.get('feedback') or request.data
        serializer = AIAnswerFeedbackSerializer(data=data)
        if serializer.is_valid():
            try:
                # set user if not provided
                if serializer.validated_data.get('user') is None:
                    serializer.save(user=request.user)
                else:
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error saving AI feedback: {e}")
                return Response({'error': 'Failed to save AI feedback.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CopyAnswersView(APIView):
    """
    POST: Copy answers from a source ProductModel to a target ProductModel.
    Both models must have the same questionnaires assigned.
    Requires: Manufacturing User or Admin
    """
    def get_permissions(self):
        return [permission() for permission in [CanAnswerQuestions]]

    def post(self, request):
        user = request.user
        if not can_user_answer_questions(user):
            return Response({'error': 'You do not have permission to copy answers.'}, status=status.HTTP_403_FORBIDDEN)

        source_model_id = request.data.get('source_model_id')
        target_model_id = request.data.get('target_model_id')

        if not source_model_id or not target_model_id:
            return Response({'error': 'source_model_id and target_model_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            source_model = ProductModel.objects.get(id=source_model_id)
            target_model = ProductModel.objects.get(id=target_model_id)
        except ProductModel.DoesNotExist as e:
            return Response({'error': f'ProductModel not found: {str(e)}'}, status=status.HTTP_404_NOT_FOUND)

        # Validate that both models have the same questionnaires assigned
        source_questionnaires = set(
            QuestionnaireEntity.objects.filter(product_entity=source_model).values_list('questionnaire_id', flat=True)
        )
        target_questionnaires = set(
            QuestionnaireEntity.objects.filter(product_entity=target_model).values_list('questionnaire_id', flat=True)
        )

        if source_questionnaires != target_questionnaires:
            return Response({
                'error': 'Source and target models must have the same questionnaires assigned.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Fetch all answers for the source model
                source_answers = Answer.objects.filter(product_entity=source_model)

                # Delete existing answers for target model (to avoid conflicts)
                Answer.objects.filter(product_entity=target_model).delete()

                # Create new answers for the target model
                new_answers = []
                for answer in source_answers:
                    new_answer = Answer(
                        is_true=answer.is_true,
                        is_false=answer.is_false,
                        source=answer.source,
                        context=answer.context,
                        option=answer.option,
                        product_entity=target_model,
                        answered_by=user
                    )
                    new_answers.append(new_answer)

                Answer.objects.bulk_create(new_answers)

                return Response({
                    'message': f'Successfully copied {len(new_answers)} answers from {source_model.name} to {target_model.name}.',
                    'copied_count': len(new_answers)
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error copying answers from model {source_model_id} to {target_model_id}: {str(e)}")
            return Response({'error': f'Error copying answers: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([CanAnswerQuestions])
def get_answerable_models_for_product_line(request, product_line_id):
    """
    GET: Get all ProductModels in a ProductLine that have answered questionnaires.
    These can be used as source models for copying answers.
    Requires: Manufacturing User or Admin
    """
    try:
        from ..models.products import ProductLine
        product_line = ProductLine.objects.get(id=product_line_id)
    except ProductLine.DoesNotExist:
        return Response({'error': 'ProductLine not found.'}, status=status.HTTP_404_NOT_FOUND)

    models = ProductModel.objects.filter(product_line=product_line, isAnswered=True).values(
        'id', 'name', 'overall_score'
    )

    return Response(list(models), status=status.HTTP_200_OK)
