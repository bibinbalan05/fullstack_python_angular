from django.core.exceptions import FieldError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import (ProductModel, MyProducts, ProductCategory, QuestionnaireCategory, ProductLine, ProductBrand, UserProfile)
from ..serializers import ProductReadSerializer
import logging
from .permissions import IsAuthenticated

# Import AllowAny for public views
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q # For complex lookups (searching)
from decimal import Decimal, InvalidOperation # For score filtering validation

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



# Use DRF's default PageNumberPagination for simplicity
class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100



# --- DRF + django-filter refactor ---
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, CharFilter, BaseInFilter

from rest_framework.filters import SearchFilter, OrderingFilter

# ProductFilter class for django-filter integration
class ProductFilter(FilterSet):
    min_score = NumberFilter(field_name="overall_score", lookup_expr="gte")
    max_score = NumberFilter(field_name="overall_score", lookup_expr="lte")
    category_names = BaseInFilter(field_name="product_line__product_category__name", lookup_expr="in")
    questionnaire_category_ids = BaseInFilter(field_name="product_line__product_category__questionnaire_category__id", lookup_expr="in")
    line_ids = BaseInFilter(field_name="product_line__id", lookup_expr="in")
    brand_ids = BaseInFilter(field_name="product_line__brand_fk_id", lookup_expr="in")

    class Meta:
        model = ProductModel
        fields = ["min_score", "max_score", "category_names", "questionnaire_category_ids", "line_ids", "brand_ids"]


class ProductSearchView(ListAPIView):
    """
    GET: Search and filter products with pagination.
    Uses django-filter and DRF's built-in pagination, search, and ordering.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductReadSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "eans__ean", "product_line__brand_fk__name", "product_line__name"]
    ordering_fields = ["id", "overall_score"]
    ordering = ["id"]

    def get_queryset(self):
        # Get user's company and my products
        user = self.request.user
        user_company = None
        my_product_ids_set = set()
        try:
            if hasattr(user, 'profile') and user.profile.company:
                user_company = user.profile.company
                my_product_ids = MyProducts.objects.filter(company=user_company).values_list('product_id', flat=True)
                my_product_ids_set = set(my_product_ids)
        except UserProfile.DoesNotExist:
            logger.warning(f"UserProfile not found for user {user.username}.")

        queryset = ProductModel.objects.select_related(
            'product_line', 'product_line__product_category', 'product_line__brand_fk'
        ).prefetch_related('aspect_total_scores').all()

        # MyProducts filter (from query params)
        my_products_filter = self.request.query_params.get('my_products_filter')
        if my_products_filter in ["only", "others"]:
            if not user_company:
                if my_products_filter == "only":
                    queryset = queryset.none()
            else:
                if my_products_filter == "only":
                    queryset = queryset.filter(id__in=my_product_ids_set)
                elif my_products_filter == "others":
                    queryset = queryset.exclude(id__in=my_product_ids_set)

        return queryset

    def get_serializer_context(self):
        # Pass my_product_ids to serializer context for UI logic
        user = self.request.user
        my_product_ids_set = set()
        try:
            if hasattr(user, 'profile') and user.profile.company:
                user_company = user.profile.company
                my_product_ids = MyProducts.objects.filter(company=user_company).values_list('product_id', flat=True)
                my_product_ids_set = set(my_product_ids)
        except UserProfile.DoesNotExist:
            pass
        context = super().get_serializer_context()
        context['my_product_ids'] = my_product_ids_set
        return context


class getFilters(APIView):
    """
    GET: Retrieve distinct values with IDs for filtering UI elements.
         The response is an array of filter objects, each containing a name
         and a list of values (each value having an 'id' and 'name').
    Requires: Any Authenticated User.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):

        # --- ProductCategory Handling (using 'name' as identifier) ---
        # Fetch distinct names first
        # Retrieve categories actually used by existing product lines
        unique_category_names = ProductCategory.objects.filter(
            productline__isnull=False
        ).distinct().order_by('name').values_list('name', flat=True)

        # Format them into the required {id: ..., name: ...} structure
        category_values = [
            {'id': name, 'name': name} for name in unique_category_names
        ]

        # --- Brand and ProductLine Handling ---
        try:
             brand_values = list(
                 ProductBrand.objects.order_by('name').values('id', 'name')
             )
        except FieldError:
             # Fallback
             unique_brand_names = ProductBrand.objects.order_by('name').values_list('name', flat=True).distinct()
             brand_values = [{'id': name, 'name': name} for name in unique_brand_names]

        try:
             line_values = list(
                 ProductLine.objects.order_by('name').values('id', 'name', 'brand_fk')
             )
        except FieldError:
             # Fallback
             unique_line_names = ProductLine.objects.order_by('name').values_list('name', flat=True).distinct()
             line_values = [{'id': name, 'name': name} for name in unique_line_names]


        # --- Score Handling ---
        unique_scores = ProductModel.objects.exclude(overall_score__isnull=True) \
                                      .values_list('overall_score', flat=True) \
                                      .distinct() \
                                      .order_by('overall_score')
        score_values = [
            {'id': str(score), 'name': str(score)} for score in unique_scores
        ]

        # --- QuestionnaireCategory Handling ---
        # Fetch questionnaire categories that are actually used by product categories
        unique_questionnaire_categories = QuestionnaireCategory.objects.filter(
            product_categories__isnull=False
        ).distinct().order_by('name').values_list('id', 'name')

        questionnaire_category_values = [
            {'id': cat_id, 'name': cat_name} for cat_id, cat_name in unique_questionnaire_categories
        ]

        # --- Construct Response ---
        response_data = [
            {
                'name': 'My Products',
                'values': [
                    {'id': 'only', 'name': 'Only My Products'},
                    {'id': 'others', 'name': 'Others'}
                ]
            },
            {
                'name': 'Product category',
                'values': category_values
            },
            {
                'name': 'Questionnaire category',
                'values': questionnaire_category_values
            },
            {
                'name': 'Brand',
                'values': brand_values
            },
            {
                'name': 'Product line',
                'values': line_values
            },
            {
                'name': 'Score',
                'values': score_values
            }
        ]

        return Response(response_data)
