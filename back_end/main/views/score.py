from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import ProductModel, Aspect, AspectTotalScore, EAN
from ..serializers import ProductReadSerializer, AspectTotalScoreSerializer
import logging
from .permissions import IsAuthenticated
# Import AllowAny for public views
from rest_framework.permissions import AllowAny

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# API to get the AspectTotalScore for a specific Product and Aspect
class AspectTotalScoreAPIView(APIView):
    """
    GET: View aspect total score for a product model.
    Requires: Any Authenticated User (Viewer, Retail, Manufacturing, Editor, Admin)
    """
    permission_classes = [IsAuthenticated] # Accessible to any logged-in user

    """
    GET: View aspect total score for a product model.
    Requires: Any Authenticated User (Viewer, Retail, Manufacturing, Editor, Admin)
    """
    permission_classes = [IsAuthenticated] # Accessible to any logged-in user

    def get(self, request, product_id, aspect_name):
        product_model = get_object_or_404(ProductModel, id=product_id)

        # If the product is not marked as answered, the score is not applicable/available.
        if not product_model.isAnswered:
            return Response(
                {'error': f'Scores are not available for product {product_id} as it has not been processed.'},
                status=status.HTTP_404_NOT_FOUND
            )

        aspect = get_object_or_404(Aspect, name=aspect_name)
        aspect_total_score = get_object_or_404(AspectTotalScore, product_model=product_model, aspect=aspect)
        serializer = AspectTotalScoreSerializer(aspect_total_score)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductScoreView(APIView):
    """
    A public API view to retrieve a product's score by its EAN.

    * Requires no authentication.
    * Requires no permissions.
    * Accessible via GET request to /api/public/product-score/{ean}/
    """
    # Override class attributes to disable authentication and permissions
    authentication_classes = [] # No authentication required
    permission_classes = [AllowAny] # Allow any user (authenticated or not)

    def get(self, request, ean, format=None):
        """
        Return the score for a product based on its EAN.
        """
        try:
            ean_obj = get_object_or_404(EAN, ean=ean)
            product = ean_obj.product_model

            # Conditionally fetch and serialize scores based on isAnswered flag
            if product.isAnswered:
                # Get aspect scores with aspect details
                aspect_scores = AspectTotalScore.objects.filter(
                    product_model=product
                ).select_related('aspect')
                aspect_serializer = AspectTotalScoreSerializer(aspect_scores, many=True)
                overall_score = product.overall_score
                aspect_scores_data = aspect_serializer.data
            else:
                # If not answered, scores are not applicable.
                overall_score = None
                aspect_scores_data = None


            response_data = {
                'product_id': product.id,
                'product_name': product.name,
                'ean': ean_obj.ean,
                'ean_name': ean_obj.name,
                'isAnswered': product.isAnswered,
                'overall_score': overall_score,
                'aspect_scores': aspect_scores_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except EAN.DoesNotExist:
            return Response(
                {'error': 'EAN not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SetScoreAnsweredView(APIView):
    """
    POST: Mark a product (identified by EAN) as answered.
    Requires: Any Authenticated User
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        ean_value = request.data.get('ean')
        if not ean_value:
            return Response(
                {'error': 'EAN is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ean_obj = get_object_or_404(EAN, ean=ean_value)
        product = ean_obj.product_model

        # Produkt als beantwortet markieren
        product.isAnswered = True
        product.save(update_fields=['isAnswered'])

        logger.info(f"Product {product.id} (EAN: {ean_value}) marked as answered")

        return Response(
            {
                'message': f'Product {product.id} marked as answered',
                'product_id': product.id,
                'ean': ean_value
            },
            status=status.HTTP_200_OK
        )


class SetScoreNAView(APIView):
    """
    POST: Mark a product (identified by EAN) as not answered.
    Requires: Any Authenticated User
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        ean_value = request.data.get('ean')
        if not ean_value:
            return Response(
                {'error': 'EAN is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ean_obj = get_object_or_404(EAN, ean=ean_value)
        product = ean_obj.product_model

        # Produkt als nicht beantwortet markieren
        product.isAnswered = False
        product.save(update_fields=['isAnswered'])

        logger.info(f"Product {product.id} (EAN: {ean_value}) marked as not answered")

        return Response(
            {
                'message': f'Product {product.id} marked as not answered',
                'product_id': product.id,
                'ean': ean_value
            },
            status=status.HTTP_200_OK
        )
