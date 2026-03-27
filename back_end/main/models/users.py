from datetime import timedelta
from django.utils import timezone
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import logging


logger = logging.getLogger(__name__)

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, related_name="profiles")
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, blank=True)
    product_brand = models.ForeignKey('main.ProductBrand', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
            else:
                logger.warning("Password check failed for user")
        except User.DoesNotExist:
            logger.warning(f"User with email {email} does not exist")
        return None

class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    can_edit_question_answers = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class SignupToken(models.Model):
    """
    Stores a temporary token for user signups, pre-associating
    the new user with a specific Role, Brand, and Company.
    """
    token = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique token sent to the user for signup."
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        help_text="The role the new user will be assigned."
    )
    brand = models.ForeignKey(
        'main.ProductBrand',
        on_delete=models.CASCADE,
        help_text="The brand the new user will be associated with."
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        help_text="The company the new user will belong to."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the token was created."
    )
    expires_at = models.DateTimeField(
        help_text="Timestamp when the token will expire."
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Indicates if the token has already been used for signup."
    )

    def save(self, *args, **kwargs):
        # Automatically set expiry date if not set (e.g., 7 days from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Checks if the token is still valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        status = "Used" if self.is_used else "Valid" if self.is_valid() else "Expired"
        return f"Signup Token for {self.company.name} / {self.brand.name} / {self.role.name} ({status})"

    class Meta:
        verbose_name = "Signup Token"
        verbose_name_plural = "Signup Tokens"
        ordering = ['-created_at'] # Show newest tokens first in admin/queries
