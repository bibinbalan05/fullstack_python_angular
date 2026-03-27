from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import (
    SignupToken, Company, Aspect, Subaspect, ProductCategory, QuestionnaireCategory, Questionnaire,
    ProductEntity, ProductBrand, ProductLine, ProductModel, QuestionnaireEntity,
    Score, Question, Option, Answer, MyProducts, Query, Suggestion,
    AspectTotalScore, UserProfile, Role, EAN, AIAnswerFeedback
)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'company', 'product_brand')
    search_fields = ('user__username', 'role__name', 'company__name', 'product_brand__name')
    list_filter = ('role',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Aspect)
class AspectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    fields = ('name',)


@admin.register(Subaspect)
class SubaspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'aspect')
    search_fields = ('name', 'aspect__name')
    list_filter = ('aspect',)


@admin.register(QuestionnaireCategory)
class QuestionnaireCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'questionnaire_category')
    search_fields = ('name',)
    list_filter = ('questionnaire_category',)


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'questionnaire_category', 'aspect', 'entity_type')
    list_filter = ('questionnaire_category', 'aspect', 'entity_type')
    search_fields = ('id',)


@admin.register(ProductEntity)
class ProductEntityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', )


@admin.register(ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand_fk', 'product_category')
    search_fields = ('name', 'brand_fk__name', 'product_category__name')
    list_filter = ('product_category', 'brand_fk')


class EANInline(admin.TabularInline):
    model = EAN
    extra = 1 # Show one empty form for a new EAN by default


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_line', 'overall_score', 'image_tag')
    search_fields = ('name', 'product_line__name')
    list_filter = ('product_line',)
    inlines = [EANInline]
    readonly_fields = ('overall_score', 'image_tag')

    def image_tag(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
            except Exception:
                return 'Image Error'
        else:
            return 'No Image'
    image_tag.short_description = 'Image'


@admin.register(EAN)
class EANAdmin(admin.ModelAdmin):
    list_display = ('ean', 'name', 'product_model')
    search_fields = ('ean', 'name', 'product_model__name')
    list_filter = ('product_model__product_line',)
    fields = ('ean', 'name', 'product_model')


@admin.register(QuestionnaireEntity)
class QuestionnaireEntityAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'product_entity')
    search_fields = ('questionnaire__entity_type', 'product_entity__name')

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except ValidationError as e:
            form.add_error(None, e.message)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_entity', 'aspect', 'value')
    search_fields = ('product_entity__name', 'aspect__name')
    list_filter = ('aspect',)


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text', 'max_score', 'subaspect', 'questionnaire')
    search_fields = ('question_text',)
    list_filter = ('subaspect', 'questionnaire')
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'option_text', 'weight', 'question')
    search_fields = ('option_text',)
    list_filter = ('question',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_entity', 'option', 'is_true', 'is_false', 'answered_by')
    search_fields = ('product_entity__name', 'option__option_text', 'answered_by__username')
    list_filter = ('is_true', 'is_false')

    def get_queryset(self, request):
        # Add custom annotations for better display
        qs = super().get_queryset(request)
        return qs.select_related('product_entity', 'option', 'answered_by')


@admin.register(MyProducts)
class MyProductsAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'product')
    search_fields = ('company__name', 'product__name')
    list_filter = ('company',)


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'retail_user', 'question', 'is_handled')
    search_fields = ('retail_user__username', 'question__question_text')
    list_filter = ('is_handled',)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'suggested_answer', 'retail_user', 'answer')
    search_fields = ('retail_user__username', 'answer__option__option_text')
    list_filter = ('answer',)


@admin.register(AspectTotalScore)
class AspectTotalScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_model', 'aspect', 'value')
    search_fields = ('product_model__name', 'aspect__name')
    list_filter = ('aspect',)

@admin.register(AIAnswerFeedback)
class AIAnswerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_entity', 'option', 'predicted_value', 'corrected_value', 'model_name', 'user', 'created_at')
    search_fields = ('model_name',)
    list_filter = ('model_name', 'predicted_value', 'corrected_value', 'created_at')

@admin.register(SignupToken)
class SignupTokenAdmin(admin.ModelAdmin):
    """
    Customizes the Django admin interface for the SignupToken model.
    """

    list_display = (
        'token_short',        # Show a shortened version of the token
        'company',
        'brand',
        'role',
        'is_valid_display',   # Show validity status clearly
        'expires_at',
        'is_used',
        'created_at',
    )
    list_filter = (
        'is_used',
        'expires_at',
        'created_at',
        'role',               # Filter by associated Role
        'brand',              # Filter by associated Brand
        'company',            # Filter by associated Company
    )
    search_fields = (
        'token__iexact',      # Allow searching by the full token (case-insensitive UUID)
        'company__name',      # Search by related company name
        'brand__name',        # Search by related brand name
        'role__name',         # Search by related role name
    )
    ordering = ('-created_at',) # Show newest tokens first by default

    # --- Detail/Edit View Customization ---
    readonly_fields = (
        'token',              # Token should not be editable after creation
        'created_at',         # Timestamp is set automatically
        'is_used',            # Status should ideally be changed by the signup process, not manually
    )

    fieldsets = (
        # Organise the form fields into logical sections
        (None, {
            'fields': ('token',)
        }),
        ('Token Associations', {
            'fields': ('role', 'company', 'brand')
        }),
        ('Status and Validity', {
            'fields': ('expires_at', 'is_used', 'created_at')
        }),
    )

    # --- Custom Methods for Display ---
    def token_short(self, obj):
        """Returns the first 8 characters of the token for cleaner list display."""
        return str(obj.token)[:8] + '...'
    token_short.short_description = 'Token (Start)' # Sets the column header name

    def is_valid_display(self, obj):
        """Displays the result of the model's is_valid() method."""
        return obj.is_valid()
    is_valid_display.boolean = True # Displays a True/False
    # instead of text
    is_valid_display.short_description = 'Is Valid?' # Sets the column header name
