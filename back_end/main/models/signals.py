from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .questionnaires import Question, Option
from .products import ProductEntity
from .utils import update_transparency_score, update_product_entity_aspect_score


@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
def handle_question_change(sender, instance, **kwargs):
    """
    A Question was added or deleted — update Transparency for all
    ProductEntities that use its Questionnaire.
    """
    questionnaire = instance.questionnaire
    affected_entities = ProductEntity.objects.filter(
        questionnaires=questionnaire
    ).distinct()

    for entity in affected_entities:
        update_transparency_score(entity)

@receiver(pre_save, sender=Option)
def handle_option_weight_change(sender, instance, **kwargs):
    """
    When an Option's weight is changed, update scores for all ProductEntities
    that have answers associated with this option.
    """
    try:
        if instance.pk:  # Check if this is an update (not a new option)
            old_option = Option.objects.get(pk=instance.pk)
            # Check if weight has actually changed
            if old_option.weight != instance.weight:
                question = instance.question
                aspect = question.questionnaire.aspect
                
                # Find all product entities with answers for this option
                affected_entities = ProductEntity.objects.filter(
                    answer__option__question=question
                ).distinct()
                
                # Store the affected entities and aspect to update after save
                instance._affected_entities = list(affected_entities)
                instance._affected_aspect = aspect
    except Option.DoesNotExist:
        pass  # New option being created, nothing to update

@receiver(post_save, sender=Option)
def update_scores_after_option_change(sender, instance, **kwargs):
    """
    After the option is saved, update scores for affected entities.
    """
    if hasattr(instance, '_affected_entities') and hasattr(instance, '_affected_aspect'):
        for entity in instance._affected_entities:
            update_product_entity_aspect_score(entity, instance._affected_aspect)

@receiver(pre_save, sender=Question)
def handle_question_max_score_change(sender, instance, **kwargs):
    """
    When a Question's max_score is changed, update scores for all ProductEntities
    that have answers associated with options for this question.
    """
    try:
        if instance.pk:  # Check if this is an update (not a new question)
            old_question = Question.objects.get(pk=instance.pk)
            # Check if max_score has actually changed
            if old_question.max_score != instance.max_score:
                aspect = instance.questionnaire.aspect
                
                # Find all product entities with answers for this question
                affected_entities = ProductEntity.objects.filter(
                    answer__option__question=instance
                ).distinct()
                
                # Store the affected entities and aspect to update after save
                instance._affected_entities = list(affected_entities)
                instance._affected_aspect = aspect
    except Question.DoesNotExist:
        pass  # New question being created, nothing to update

@receiver(post_save, sender=Question)
def update_scores_after_question_change(sender, instance, **kwargs):
    """
    After the question is saved, update scores for affected entities.
    """
    if hasattr(instance, '_affected_entities') and hasattr(instance, '_affected_aspect'):
        for entity in instance._affected_entities:
            update_product_entity_aspect_score(entity, instance._affected_aspect)