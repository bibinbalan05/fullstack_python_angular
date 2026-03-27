from rest_framework import serializers
from django.db import transaction
from ..models import (
    ProductModel, ProductBrand, ProductLine, ProductCategory,
    MyProducts, ProductEntity, EAN, QuestionnaireEntity, Question, Query
)
from .scoring import AspectTotalScoreSerializer
from ..views.permissions import can_user_answer_questions

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBrand
        fields = ['id', 'name']

class EANSerializer(serializers.ModelSerializer):
    class Meta:
        model = EAN
        fields = ['id', 'ean', 'name']

class ProductLineSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand_fk.name', read_only=True)

    class Meta:
        model = ProductLine
        fields = ['id', 'name', 'product_category', 'brand_fk', 'brand_name']

class ProductReadSerializer(serializers.ModelSerializer):
    product_line_name = serializers.CharField(source='product_line.name', read_only=True)
    product_category = serializers.CharField(source='product_line.product_category.name', read_only=True)
    aspect_scores = serializers.SerializerMethodField()
    product_line = ProductLineSerializer(read_only=True)
    eans = EANSerializer(many=True, read_only=True)
    is_my_product = serializers.SerializerMethodField()
    concern_count = serializers.SerializerMethodField()
    overall_score = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = [
            'id', 'name', 'product_line', 'product_line_name',
            'product_category', 'overall_score', 'aspect_scores',
            'image', 'eans', 'is_my_product', 'concern_count', "isAnswered",
        ]

    def get_overall_score(self, obj):
        # Return score only if the product is answered
        return obj.overall_score if obj.isAnswered else None

    def get_aspect_scores(self, obj):
        # Return aspect scores only if the product is answered
        if obj.isAnswered:
            scores = obj.aspect_total_scores.all()
            return AspectTotalScoreSerializer(scores, many=True).data
        return None

    def get_is_my_product(self, obj):
        my_product_ids = self.context.get('my_product_ids')
        if my_product_ids is not None and obj.id in my_product_ids:
            return True
        return False

    def get_concern_count(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None

        try:
            # Use the centralized permission helper. If the user can't answer, no need to count.
            if not can_user_answer_questions(user):
                return 0

            # Collect all related entities (ProductModel, ProductLine, ProductBrand)
            entities_to_check = [obj]
            if obj.product_line:
                entities_to_check.append(obj.product_line)
                if obj.product_line.brand_fk:
                    entities_to_check.append(obj.product_line.brand_fk)
            

            # Get all questionnaires linked to these entities
            questionnaire_ids = QuestionnaireEntity.objects.filter(
                product_entity__in=entities_to_check
            ).values_list('questionnaire_id', flat=True)
            
            # Count all unhandled queries associated with the product's question hierarchy.
            return Query.objects.filter(
                question__questionnaire_id__in=questionnaire_ids,
                is_handled=False
            ).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating concern_count for product {obj.id}: {str(e)}")
            return 0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get('request').user if self.context.get('request') else None
 
        # Use the centralized permission helper to decide if the count should be shown
        if not can_user_answer_questions(user):
            data.pop('concern_count', None)
 
        return data


class ProductWriteListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        with transaction.atomic():
            instances = [
                self.child.create(item) for item in validated_data
            ]
        return instances

    def update(self, instances, validated_data):
        raise NotImplementedError

class EANWriteSerializer(serializers.ModelSerializer):
    # Explicitly define product_model to make it optional.
    # It's required for creation but not for updates, as an EAN's product doesn't change.
    product_model = serializers.PrimaryKeyRelatedField(
        queryset=ProductModel.objects.all(), required=False
    )

    class Meta:
        model = EAN
        fields = ('id', 'ean', 'name', 'product_model')

    def validate_ean(self, value):
        ean_id = self.instance.pk if self.instance else None
        if EAN.objects.exclude(pk=ean_id).filter(ean=value).exists():
            raise serializers.ValidationError(
                f"EAN '{value}' is already in use by another product variant."
            )
        return value

class ProductWriteSerializer(serializers.ModelSerializer):
    productLineID = serializers.PrimaryKeyRelatedField(
        source='product_line',
        queryset=ProductLine.objects.all(),
        write_only=True
    )
    eans = EANWriteSerializer(many=True, required=False, read_only=True)
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'productLineID', 'image', 'eans')
        list_serializer_class = ProductWriteListSerializer

    def validate_image(self, value):
        """
        Ensure the image path is a string and points to the 'products/' directory
        for security. An empty string or null is allowed to clear the image.
        """
        if value and (not isinstance(value, str) or not value.startswith('products/')):
            raise serializers.ValidationError("Invalid image path. Must be a path to an image in the products directory.")
        # Allow empty string to clear the image, which will be saved as None/empty in the model.
        return value

    def create(self, validated_data):
        # Get eans data from initial_data since the field is now read_only
        # Handle both single item (dict) and bulk create (list) cases
        if isinstance(self.initial_data, dict):
            eans_data = self.initial_data.get('eans', []) or []
        elif isinstance(self.initial_data, list):
            # This shouldn't happen in normal operation, but handle it defensively
            eans_data = []
        else:
            eans_data = []
        product = ProductModel.objects.create(**validated_data)

        # Create EANs for the product
        for ean_data in eans_data:
            ean_serializer = EANWriteSerializer(data={**ean_data, 'product_model': product.pk})
            ean_serializer.is_valid(raise_exception=True)
            ean_serializer.save()

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        # Handle both single item (dict) and bulk update (list) cases
        if isinstance(self.initial_data, dict):
            eans_data = self.initial_data.get('eans')
        elif isinstance(self.initial_data, list):
            # This shouldn't happen in normal operation, but handle it defensively
            eans_data = None
        else:
            eans_data = None
        
        # The 'eans' field is read_only, so we pop it from validated_data to avoid issues with super().update()
        validated_data.pop('eans', None)
        # Let the default update handle simple fields like 'name', 'product_line', and 'image'.
        instance = super().update(instance, validated_data)
        instance.save()

        # Update EANs if provided
        if eans_data is not None:
            # Get IDs of EANs from the incoming data
            incoming_ean_ids = {item['id'] for item in eans_data if 'id' in item}

            # Delete EANs that are associated with the product but not in the incoming data
            instance.eans.exclude(id__in=incoming_ean_ids).delete()

            # Update existing EANs and create new ones
            for ean_data in eans_data:
                ean_id = ean_data.get('id')
                if ean_id:
                    # Update existing EAN
                    try:
                        ean_instance = EAN.objects.get(id=ean_id, product_model=instance)
                        # Pass the instance to the serializer
                        ean_serializer = EANWriteSerializer(ean_instance, data=ean_data, partial=True)
                        ean_serializer.is_valid(raise_exception=True)
                        ean_serializer.save()
                    except EAN.DoesNotExist:
                        # This case handles if an EAN ID from another product is sent, though it's unlikely with a good frontend.
                        pass
                else:
                    # Create new EAN
                    ean_serializer = EANWriteSerializer(data={**ean_data, 'product_model': instance.pk})
                    ean_serializer.is_valid(raise_exception=True)
                    ean_serializer.save()

        return instance

class MyProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyProducts
        fields = ['company', 'product']

class ProductCategoryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['name']

class ProductLineNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLine
        fields = ['name']

class ProductOverallScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ['overall_score']

class ProductBrandNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBrand
        fields = ['name']
