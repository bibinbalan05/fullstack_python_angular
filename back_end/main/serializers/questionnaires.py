from rest_framework import serializers
from ..models import Question, Option, Questionnaire

class OptionSerializer(serializers.ModelSerializer):
    optionText = serializers.CharField(source='option_text')
    definition = serializers.CharField(allow_blank=True, allow_null=True)

    class Meta:
        model = Option
        fields = ['id', 'optionText', 'weight', 'definition']

class QuestionSerializer(serializers.ModelSerializer):
    questionText = serializers.CharField(source='question_text')
    purpose = serializers.CharField(allow_blank=True, allow_null=True)
    maxScore = serializers.FloatField(source='max_score')
    subAspect = serializers.CharField(source='subaspect')
    options = OptionSerializer(many=True, read_only=True, source='option_set')
    isSingleChoice = serializers.BooleanField(source='is_single_choice')
    instructions = serializers.CharField(allow_blank=True, allow_null=True)

    class Meta:
        model = Question
        fields = ['id', 'questionText', 'purpose', 'maxScore', 'subAspect', 'options', 'isSingleChoice', 'instructions']

class QuestionnaireSerializer(serializers.ModelSerializer):
    questionnaireCategory = serializers.CharField(source='questionnaire_category')
    entityType = serializers.CharField(source='entity_type')
    questions = QuestionSerializer(many=True, read_only=True, source='question_set')

    class Meta:
        model = Questionnaire
        fields = ['id', 'questionnaireCategory', 'aspect', 'entityType', 'questions']
