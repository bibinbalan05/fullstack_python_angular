from rest_framework import serializers
from ..models import Aspect, AspectTotalScore, Answer, Suggestion, ProductEntity, User, AIAnswerFeedback, Option

class AspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aspect
        fields = ["name"]

class AspectTotalScoreSerializer(serializers.ModelSerializer):
    aspect = AspectSerializer(read_only=True)
    class Meta:
        model = AspectTotalScore
        fields = ["aspect", "value",]

class AnswerSerializer(serializers.ModelSerializer):
    isTrue = serializers.BooleanField(source="is_true")
    isFalse = serializers.BooleanField(source="is_false")
    productEntityId = serializers.PrimaryKeyRelatedField(
        queryset=ProductEntity.objects.all(), source="product_entity"
    )
    answeredBy = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="answered_by"
    )
    class Meta:
        model = Answer
        fields = ['id', 'isTrue', 'isFalse', 'source', 'context', 'option', 'productEntityId', 'answeredBy']

    def validate(self, data):
        """Custom validation for the AnswerSerializer.

        - Source (BibTeX) is optional for manual answers.
        - If source is provided, it will be validated and normalized.
        - Source should ideally contain the quote/context as a note field in the BibTeX entry.
        """
        source = data.get("source", "").strip() if data.get("source") else ""
        context = data.get("context", "").strip() if data.get("context") else ""
        
        # Validate and normalize source BibTeX if provided
        if source:
            from ..models.utils import ValidationError as DjangoValidationError
            from ..models.utils import to_bibtex
            try:
                # Normalize the incoming source to canonical BibTeX
                formatted = to_bibtex(source)
                data["source"] = formatted
            except DjangoValidationError as e:
                # Return a DRF validation error so the client can surface it
                raise serializers.ValidationError({"source": f"Invalid BibTeX format: {str(e)}"})
        else:
            data["source"] = ""
        
        # Ensure context is set (empty string if not provided) - kept for backward compatibility
        data["context"] = context
        
        return data
    
    def create(self, validated_data):
        # The model's clean() method will be called on save, enforcing all rules.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # The model's clean() method will be called on save, enforcing all rules.
        return super().update(instance, validated_data)

class SuggestionSerializer(serializers.ModelSerializer):
    suggestedAnswer = serializers.BooleanField(source="suggested_answer")
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="retail_user"
    )
    class Meta:
        model = Suggestion
        fields = ['id', 'suggestedAnswer', 'user', 'answer']


class AIAnswerFeedbackSerializer(serializers.ModelSerializer):
    productEntityId = serializers.PrimaryKeyRelatedField(queryset=ProductEntity.objects.all(), source='product_entity')
    optionId = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all(), source='option')
    predictedValue = serializers.BooleanField(source='predicted_value', allow_null=True, required=False)
    correctedValue = serializers.BooleanField(source='corrected_value', allow_null=True, required=False)
    predictedOptionId = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all(), source='predicted_option', allow_null=True, required=False)
    modelName = serializers.CharField(source='model_name', allow_blank=True, required=False)
    userId = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', allow_null=True, required=False)

    class Meta:
        model = AIAnswerFeedback
        fields = ['id', 'productEntityId', 'optionId', 'predictedValue', 'correctedValue', 'predictedOptionId', 'modelName', 'userId', 'created_at']
        read_only_fields = ['id', 'created_at']
