from django.db import models
from django.db.models import Q
from decimal import Decimal
import logging

from pybtex.database import BibliographyData, Entry
from django.core.exceptions import ValidationError
from pybtex.exceptions import PybtexError
from pybtex.database.input.bibtex import Parser as BibtexParser
from pybtex.database.output.bibtex import Writer as BibtexWriter
from io import StringIO

logger = logging.getLogger(__name__)


def calculate_product_entity_aspect_score(product_entity, aspect):
    """
    Calculates the weighted score for a specific aspect of a given ProductEntity.
    Only answers marked as is_true=True contribute to the score.
    """
    from .questionnaires import QuestionnaireEntity, Question
    from .scoring import Answer

    questionnaire_entities = QuestionnaireEntity.objects.filter(
        product_entity=product_entity,
        questionnaire__aspect=aspect
    )

    if not questionnaire_entities.exists():
        logger.warning(f"No QuestionnaireEntity for entity={product_entity.id}, aspect={aspect.name}")
        return 0.0

    total_score = 0.0

    for questionnaire_entity in questionnaire_entities:
        questions = Question.objects.filter(questionnaire=questionnaire_entity.questionnaire)

        for question in questions:
            true_answers = Answer.objects.filter(
                product_entity=product_entity,
                option__question=question,
                is_true=True
            )
            question_score = sum(answer.option.weight for answer in true_answers)
            capped_score = min(question_score, question.max_score)
            total_score += capped_score

    return total_score

def update_product_entity_aspect_score(product_entity, aspect):
    """
    Updates or creates a Score entry for the given ProductEntity and Aspect.

    Delegates score calculation to `calculate_product_entity_aspect_score()`,
    then stores the result in the Score table.
    """
    from .scoring import Score

    score_value = calculate_product_entity_aspect_score(product_entity, aspect)
    score, created = Score.objects.update_or_create(
        product_entity=product_entity,
        aspect=aspect,
        defaults={'value': score_value}
    )
    logger.info(f"{'Created' if created else 'Updated'} Score for entity={product_entity.id}, aspect={aspect.name}, value={score.value}")

def calculate_transparency_score(product_entity) -> Decimal:
    """
    Calculates the transparency score for a ProductEntity.
    A question is considered answered if it has at least one answer
    marked as either is_true=True or is_false=True.
    """
    from .questionnaires import QuestionnaireEntity, Question
    from .scoring import Answer

    """
    Compute the transparency score for a single entity (Brand, Line or Model).

    The per-entity score is: (answered_questions / total_questions) * 10
    Only questions assigned to that entity's questionnaires are considered.
    Returns a Decimal rounded to 2 decimal places.
    """
    q_ids = QuestionnaireEntity.objects.filter(
        product_entity=product_entity
    ).values_list("questionnaire", flat=True)

    total_q = Question.objects.filter(questionnaire_id__in=q_ids).count()
    if total_q == 0:
        return Decimal("0")

    # A question is answered if it has at least one answer with is_true=True or is_false=True
    answered_q = (
        Answer.objects
        .filter(product_entity=product_entity,
                option__question__questionnaire_id__in=q_ids)
        .filter(Q(is_true=True) | Q(is_false=True))
        .values("option__question")
        .distinct()
        .count()
    )

    score = Decimal(answered_q) / Decimal(total_q) * Decimal("10")
    return score.quantize(Decimal("0.01"))

def update_transparency_score(product_entity):
    """
    Updates or creates the transparency Score entry for the given ProductEntity.

    This uses `calculate_transparency_score()`,
    then stores the result in the Score table.
    """
    from .aspects import Aspect
    from .scoring import Score

    aspect = Aspect.objects.get(name="Transparency")
    value  = calculate_transparency_score(product_entity)

    score, _ = Score.objects.update_or_create(
        product_entity=product_entity,
        aspect=aspect,
        defaults={"value": value},
    )
    logger.info(
        "Transparency score for entity=%s updated to %.2f",
        product_entity.id, score.value
    )

def update_aspect_total_score(product, aspect):
    """
    Updates or creates the total score for a specific aspect of a ProductModel.

    This aggregates the individual aspect scores of the ProductModel, its ProductLine,
    and its Brand, and stores the combined score in the AspectTotalScore table.
    """
    from .scoring import Score, AspectTotalScore
    product_line = product.product_line
    brand = product_line.brand_fk

    product_score = Score.objects.filter(aspect=aspect, product_entity=product).first()
    line_score = Score.objects.filter(aspect=aspect, product_entity=product_line).first()
    brand_score = Score.objects.filter(aspect=aspect, product_entity=brand).first()

    # For Transparency aspect, the total score is the average of available
    # level scores (Brand / Line / Model), ignoring missing levels.
    if aspect.name == "Transparency":
        values = [s.value for s in (product_score, line_score, brand_score) if s is not None]
        if values:
            # average and store with one decimal place (AspectTotalScore uses 1 dp)
            total_score = (sum(values) / Decimal(len(values))).quantize(Decimal("0.1"))
        else:
            total_score = Decimal("0.0")
    else:
        total_score = sum(filter(None, [
            getattr(product_score, 'value', 0),
            getattr(line_score, 'value', 0),
            getattr(brand_score, 'value', 0)
        ]))

    # Ensure total_score is a Decimal and cap to 10.0 maximum
    if not isinstance(total_score, Decimal):
        total_score = Decimal(str(total_score))

    if total_score > Decimal("10"):
        total_score = Decimal("10.0")

    # Ensure AspectTotalScore uses one decimal place
    total_score = total_score.quantize(Decimal("0.1"))

    aspect_total, created = AspectTotalScore.objects.update_or_create(
        product_model=product,
        aspect=aspect,
        defaults={'value': total_score}
    )
    logger.info(f"AspectTotalScore for product={product.id}, aspect={aspect.name}: {aspect_total.value}")

    update_overall_score(product)

def update_overall_score(product):
    """
    Recalculates and updates the overall score of a ProductModel.

    The overall score is the average of all the Product's AspectTotalScores.
    """
    avg_score = product.aspect_total_scores.aggregate(avg=models.Avg('value'))['avg'] or 0
    rounded_score = round(avg_score, 1)
    product.overall_score = rounded_score
    product.save(update_fields=['overall_score'])
    logger.info(f"Overall score updated for product={product.id}: {product.overall_score}")


def to_bibtex(citation_text: str) -> str:
    """
    Validates and reformats a BibTeX citation string for consistency.

    This function expects a string in BibTeX format. It parses the string
    and then re-serializes it to ensure a consistent format. If the input
    is not valid BibTeX, it raises a ValidationError.

    Args:
        citation_text: The string to validate, expected to be in BibTeX format.

    Returns:
        A consistently formatted BibTeX string.

    Raises:
        ValidationError: If the citation_text is not valid BibTeX.
    """
    if not citation_text or not citation_text.strip():
        return ""

    text = citation_text.strip()

    try:
        parser = BibtexParser()
        bib_data = parser.parse_string(text)
        if not bib_data.entries:
            raise ValidationError("Source must contain at least one valid BibTeX entry.")
        writer = BibtexWriter()
        return writer.to_string(bib_data)
    except PybtexError as e:
        logger.warning(f"Could not parse BibTeX source. Error: {e}")
        raise ValidationError(f"Source is not valid BibTeX. Error: {e}") from e
