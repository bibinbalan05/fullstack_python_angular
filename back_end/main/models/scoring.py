import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from .utils import to_bibtex

logger = logging.getLogger(__name__)


class Answer(models.Model):
    is_true = models.BooleanField(default=False)
    is_false = models.BooleanField(default=False)
    source = models.TextField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    option = models.ForeignKey('main.Option', on_delete=models.CASCADE)
    product_entity = models.ForeignKey('main.ProductEntity', on_delete=models.CASCADE)
    answered_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def clean(self):
        """
        Custom model validation.
        - Ensures is_true and is_false are not both True.
        - Ensures the Option is valid for the ProductEntity's assigned questionnaires.
        """
        # Import here to avoid circular import issues if needed elsewhere
        from .questionnaires import QuestionnaireEntity

        # 1. Validate boolean fields
        if self.is_true and self.is_false:
            raise ValidationError(
                "Answer cannot be both true and false at the same time."
            )

        # 2. Validate that the Option belongs to a Questionnaire assigned to the ProductEntity
        if self.product_entity and self.option:
            is_valid_option = QuestionnaireEntity.objects.filter(
                product_entity=self.product_entity,
                questionnaire=self.option.question.questionnaire
            ).exists()

            if not is_valid_option:
                raise ValidationError(f"Option '{self.option}' is not valid for Product Entity '{self.product_entity}' because it is not part of an assigned questionnaire.")

        # 2. Validate that the Option belongs to a Questionnaire assigned to the ProductEntity
        if self.product_entity and self.option:
            is_valid_option = QuestionnaireEntity.objects.filter(
                product_entity=self.product_entity,
                questionnaire=self.option.question.questionnaire
            ).exists()

            if not is_valid_option:
                raise ValidationError(f"Option '{self.option}' is not valid for Product Entity '{self.product_entity}' because it is not part of an assigned questionnaire.")

    def save(self, *args, **kwargs):
        self.clean()  # Ensure validation runs on save

        # Import here to avoid circular imports
        from .utils import (
            update_product_entity_aspect_score,
            update_transparency_score,
        )
        # Determine whether the question had any answered answers before this save
        prev_question_answered = False
        if self.pk:
            try:
                old = Answer.objects.get(pk=self.pk)
                prev_question_answered = old.is_true or old.is_false
            except Answer.DoesNotExist:
                prev_question_answered = False

        # Also check if other answers for this question were already answered
        other_answered = Answer.objects.filter(
            product_entity=self.product_entity,
            option__question=self.option.question,
        ).exclude(pk=self.pk).filter(Q(is_true=True) | Q(is_false=True)).exists()

        prev_question_answered = prev_question_answered or other_answered

        super().save(*args, **kwargs)

        # update the normal score for this answer's aspect
        aspect = self.option.question.questionnaire.aspect
        update_product_entity_aspect_score(self.product_entity, aspect)

        # Determine whether the question has any answered answers after this save
        now_question_answered = Answer.objects.filter(
            product_entity=self.product_entity,
            option__question=self.option.question,
        ).filter(Q(is_true=True) | Q(is_false=True)).exists()

        # If answered-state for the question changed (none -> some or some -> none), update transparency
        if prev_question_answered != now_question_answered:
            update_transparency_score(self.product_entity)

    @property
    def is_answered(self):
        """Returns True if the answer has been explicitly marked as true or false."""
        return self.is_true or self.is_false

    @property
    def is_unknown(self):
        """Returns True if the answer is in the unknown state (neither true nor false)."""
        return not (self.is_true or self.is_false)

    def __str__(self):
        status = "True" if self.is_true else "False" if self.is_false else "Unknown"
        return f"Answer {self.id}: {status}"

    def delete(self, *args, **kwargs):
        # Import here to avoid circular imports
        from .utils import (
            update_product_entity_aspect_score,
            update_transparency_score,
        )

        # Store these before deletion
        product_entity = self.product_entity
        question = self.option.question
        aspect = question.questionnaire.aspect

        super().delete(*args, **kwargs)

        # Update aspect score
        update_product_entity_aspect_score(product_entity, aspect)

        # Check if this was the last answer for this question from this product entity
        has_other_answers = Answer.objects.filter(
            product_entity=product_entity,
            option__question=question,
        ).exists()

        # Only update transparency if we just removed the last answer
        if not has_other_answers:
            update_transparency_score(product_entity)


class Score(models.Model):
    aspect = models.ForeignKey("main.Aspect", on_delete=models.CASCADE)
    product_entity = models.ForeignKey("main.ProductEntity", on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ("aspect", "product_entity")

    def __str__(self):
        return f"Score {self.id} for {self.product_entity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        entity = self.product_entity.get_subclass_instance()
        the_aspect = self.aspect

        def fan_out():
            # Import locally to avoid circular imports
            from .products import ProductBrand, ProductLine, ProductModel
            from .utils import update_aspect_total_score

            if isinstance(entity, ProductModel):
                update_aspect_total_score(entity, the_aspect)

            elif isinstance(entity, ProductLine):
                for p in ProductModel.objects.filter(product_line=entity):
                    update_aspect_total_score(p, the_aspect)

            elif isinstance(entity, ProductBrand):
                lines = ProductLine.objects.filter(brand_fk=entity)
                for p in ProductModel.objects.filter(product_line__in=lines):
                    update_aspect_total_score(p, the_aspect)

        transaction.on_commit(fan_out)


# Model to store total scores per aspect for each model
class AspectTotalScore(models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    aspect = models.ForeignKey("main.Aspect", on_delete=models.CASCADE)
    product_model = models.ForeignKey(
        "main.ProductModel",
        on_delete=models.CASCADE,
        related_name="aspect_total_scores",
    )

    class Meta:
        unique_together = ("product_model", "aspect")

    def __str__(self):
        return f"{self.aspect.name} Score for {self.product_model}: {self.value}"


# New model to store AI answer feedback (prediction vs user-correction)
class AIAnswerFeedback(models.Model):
    """
    Stores a single feedback record about an AI-predicted answer and the user's correction.
    """
    product_entity = models.ForeignKey('main.ProductEntity', on_delete=models.CASCADE)
    option = models.ForeignKey('main.Option', on_delete=models.CASCADE, related_name='ai_feedbacks')
    predicted_value = models.BooleanField(null=True, blank=True)
    corrected_value = models.BooleanField(null=True, blank=True)
    predicted_option = models.ForeignKey('main.Option', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    model_name = models.CharField(max_length=200, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AIFeedback({self.id}) for entity {self.product_entity_id} option {self.option_id}"
