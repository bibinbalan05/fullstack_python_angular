from django.db import models
from django.contrib.auth.models import User
import logging
from django.core.exceptions import ValidationError

from .aspects import Aspect, Subaspect
from .utils import update_transparency_score

logger = logging.getLogger(__name__)


class Questionnaire(models.Model):
    ENTITY_TYPE_CHOICES = [
        ('ProductBrand', 'ProductBrand'),
        ('ProductLine', 'ProductLine'),
        ('ProductModel', 'ProductModel'),
    ]

    questionnaire_category = models.ForeignKey('main.QuestionnaireCategory', on_delete=models.CASCADE, null=True, blank=True)
    aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES)

    def save(self, *args, **kwargs):
        # Prevent saving a Questionnaire with Aspect 'Transparency'
        if self.aspect.name == 'Transparency':
            raise ValidationError("Questionnaire cannot be of Aspect 'Transparency'.")
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['questionnaire_category', 'aspect', 'entity_type'],
                name='unique_questionnairecategory_aspect_entitytype'
            )
        ]

    def __str__(self):
        return f'Questionnaire {self.id}: {self.entity_type} - {self.questionnaire_category} - {self.aspect}'


class QuestionnaireEntity(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    product_entity = models.ForeignKey('main.ProductEntity', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('questionnaire', 'product_entity')

    def __str__(self):
        return f"Questionnaire {self.questionnaire} for ProductEntity {self.product_entity}."

    def delete(self, *args, **kwargs):
        pe = self.product_entity
        super().delete(*args, **kwargs)
        update_transparency_score(pe)

    def clean(self):
        """Model-level validation that can be called by forms and programmatically via `full_clean()`.
        Raises structured ValidationError for field-aware errors so admin/forms can display them properly.
        """
        from .products import ProductBrand, ProductLine, ProductModel

        pe = self.product_entity.get_subclass_instance()

        # Validate entity type match
        expected = self.questionnaire.entity_type if self.questionnaire else None
        actual = type(pe).__name__ if pe else type(self.product_entity).__name__
        if expected and actual and expected != actual:
            raise ValidationError({
                'product_entity': (
                    f"Product entity is of type '{actual}' but questionnaire expects entity type '{expected}'."
                )
            })

        # Questionnaire category consistency validation for ProductModels
        if isinstance(pe, ProductModel):
            product = pe
            product_line = product.product_line

            # Ensure product_line's product_category exists
            if product_line.product_category is None:
                raise ValidationError({'product_entity': f"ProductLine '{product_line}' has no product category assigned."})

            # Ensure product_line's product_category has a questionnaire_category
            if product_line.product_category.questionnaire_category is None:
                raise ValidationError({'product_entity': f"ProductCategory '{product_line.product_category}' has no questionnaire category assigned."})

            # Validate questionnaire category consistency
            if self.questionnaire.questionnaire_category != product_line.product_category.questionnaire_category:
                raise ValidationError({
                    'questionnaire': (
                        f"ProductModel '{product}' cannot be associated with a questionnaire for category "
                        f"'{self.questionnaire.questionnaire_category}' because its product line "
                        f"'{product_line}' belongs to product category '{product_line.product_category}' "
                        f"which is under questionnaire category '{product_line.product_category.questionnaire_category}'."
                    )
                })

        # Ensure no duplicate entries for the same questionnaire and product entity combination
        qs = QuestionnaireEntity.objects.filter(questionnaire=self.questionnaire,
                                                product_entity=self.product_entity)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError({'__all__': "This questionnaire is already associated with this product entity."})

    def save(self, *args, **kwargs):
        # Run model-level validation before saving so callers that don't call full_clean get consistent errors
        self.clean()

        # Call the superclass save method to handle the actual save
        super().save(*args, **kwargs)
        update_transparency_score(self.product_entity)


class Question(models.Model):
    question_text = models.TextField()
    purpose = models.TextField(blank=True, null=True)
    max_score = models.FloatField()
    subaspect = models.ForeignKey(Subaspect, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    is_single_choice = models.BooleanField(default=False, help_text="If true, only one option can be selected (single-choice). If false, multiple options can be selected.")
    instructions = models.TextField(blank=True, null=True, help_text="Specific instructions for the AI on how to answer this question.")

    def __str__(self):
        return f'Question {self.id}: {self.question_text}'

class Option(models.Model):
    option_text = models.TextField()
    weight = models.FloatField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    definition = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Option {self.id}: {self.option_text}'


class Query(models.Model):
    is_handled = models.BooleanField(default=False)
    retail_user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    suggestion_text = models.TextField(blank=True, default='')

    def __str__(self):
        return f'Query {self.id}'

class Suggestion(models.Model):
    suggested_answer = models.BooleanField()
    retail_user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey('main.Answer', on_delete=models.CASCADE)

    def __str__(self):
        return f'Suggestion {self.id} by {self.retail_user}: {self.answer.option} to {self.suggested_answer}'
