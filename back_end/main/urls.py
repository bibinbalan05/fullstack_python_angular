from django.urls import path

from .views.auth import GetCSRFToken, LoginUserView, LogoutUserView, PasswordResetConfirmView, PasswordResetRequestView
from .views.filters import ProductSearchView, getFilters
from .views.products import ProductView, BrandView, ProductLineView, MyProductsView, ProductCategories, SustainabilityReportView
from .views.media_images import MediaImagesView
from .views.questionnaire import Answers, get_entity_questionnaires, Suggestion, QueryView, CopyAnswersView, get_answerable_models_for_product_line, AIAnswerFeedbackView
from .views.score import AspectTotalScoreAPIView, ProductScoreView, SetScoreAnsweredView, SetScoreNAView

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # API to get AspectTotalScore for a specific Model and Aspect
    path('models/<int:model_id>/aspects/<str:aspect_name>/score/', AspectTotalScoreAPIView.as_view(), name='aspect-total-score'),

    path('models/products/', ProductView.as_view(), name='product-list'),
    path('models/products/<int:product_id>/', ProductView.as_view(), name='product-detail'),
    path('models/products/<int:product_id>/sustainability-report/', SustainabilityReportView.as_view(), name='sustainability-report-upload'),
    path('models/products/search/', ProductSearchView.as_view(), name='product-search'),

    path('models/brands/<int:brand_id>/', BrandView.as_view(), name='brand-detail'),
    path('models/brands/', BrandView.as_view(), name='brand-list'),

    path('models/productlines/<int:product_line_id>/', ProductLineView.as_view(), name='productline-detail'),
    path('models/productlines/', ProductLineView.as_view(), name='productline-list'),

    path('models/myproducts/', MyProductsView.as_view(), name='model-my-products'),

    path('models/myproducts/<str:company_name>/', MyProductsView.as_view(), name='model-my-products-detail'),

    path('models/all-filters/', getFilters.as_view(), name='all-filters'),

    path('models/productcategory/', ProductCategories.as_view(), name='model-ProductCategories'),

    # Media images listing and upload
    path('media/images/', MediaImagesView.as_view(), name='media-images'),

    path('models/questionnaire-entity/<int:entity_id>/', get_entity_questionnaires, name='get_entity_questionnaires'),

    path('models/answer/<int:product_entity_id>', Answers.as_view(), name='model-answer'),

    path('models/answer/<int:product_entity_id>/<int:answer_id>', Answers.as_view(), name='model-answer-detail'),

    path('models/suggestion/', Suggestion.as_view(), name='model-suggestion'),

    path('models/ai-feedback/', AIAnswerFeedbackView.as_view(), name='model-ai-feedback'),

    path('models/query/', QueryView.as_view(), name='model-query'),
    path('models/query/<int:query_id>/', QueryView.as_view(), name='model-query-detail'),

    path('models/answers/copy/', CopyAnswersView.as_view(), name='copy-answers'),
    path('models/productlines/<int:product_line_id>/answerable-models/', get_answerable_models_for_product_line, name='get-answerable-models'),

    path('public/product-score/<str:ean>/', ProductScoreView.as_view(), name='public_product_score'),

    path('score/answered', SetScoreAnsweredView.as_view(), name='set_score_answered'),

    path('score/na', SetScoreNAView.as_view(), name='set_score_na'),

    path('login/', LoginUserView.as_view(), name='login'),

    path('logout/', LogoutUserView.as_view(), name='logout'),

    path('password-reset/request/', PasswordResetRequestView.as_view(), name='api_password_reset_request'),

    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='api_password_reset_confirm'),

    path('csrf/', GetCSRFToken.as_view(), name='api-csrf'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
