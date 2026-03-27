from rest_framework import serializers
from ..models import UserProfile, User, Company

class CompanySerializer(serializers.ModelSerializer):
    canEditQuestionAnswers = serializers.BooleanField(source='can_edit_question_answers')

    class Meta:
        model = Company
        fields = ['name', 'canEditQuestionAnswers']

class UserProfileSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    roleName = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['company', 'role', 'roleName', 'product_brand']

    def get_roleName(self, obj):
        try:
            return obj.role.name if obj.role else None
        except Exception:
            return None

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()  # Include the profile
    canAnswerQuestions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'profile', 'canAnswerQuestions']

    def get_canAnswerQuestions(self, user):
        try:
            # Admins can always answer
            role = getattr(user.profile.role, 'name', None)
            if role == 'Admin':
                return True

            # ManufacturingUser must also have company.can_edit_question_answers
            if role == 'ManufacturingUser':
                company = getattr(user.profile, 'company', None)
                return bool(company and getattr(company, 'can_edit_question_answers', False))

            return False
        except Exception:
            return False

class CompaniesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name']
