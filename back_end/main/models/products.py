from django.db import models
import logging
from main.validators import EanValidator

from .users import Company

logger = logging.getLogger(__name__)

class QuestionnaireCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Questionnaire Category"
        verbose_name_plural = "Questionnaire Categories"


class ProductCategory(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    questionnaire_category = models.ForeignKey(
        QuestionnaireCategory,
        on_delete=models.CASCADE,
        related_name='product_categories',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class ProductEntity(models.Model):
    name = models.CharField(max_length=255)
    questionnaires = models.ManyToManyField('main.Questionnaire', through='main.QuestionnaireEntity')

    def get_subclass_instance(self):
        if hasattr(self, 'productbrand'):
            return self.productbrand
        elif hasattr(self, 'productline'):
            return self.productline
        elif hasattr(self, 'productmodel'):
            return self.productmodel
        return self

    def __str__(self):
        return self.name

class ProductBrand(ProductEntity):

    def __str__(self):
        return self.name

class ProductLine(ProductEntity):
    brand_fk = models.ForeignKey(ProductBrand, on_delete=models.CASCADE)
    product_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.brand_fk} {self.name}'


class ProductModel(ProductEntity):
    product_line = models.ForeignKey(ProductLine, on_delete=models.CASCADE)
    overall_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    isAnswered = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Ensure a default image is used if none is provided
        # If no image is provided, leave the field empty (null) so that
        # callers can detect an absent image and fallback to frontend placeholder.
        # Assigning a raw string to an ImageField can cause problems with storage
        # backends that expect File objects or a storage-managed name.
        if not self.image:
            self.image = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product_line} {self.name}'


class EAN(models.Model):
    ean = models.CharField(
        max_length=15,
        unique=True,
        help_text=("Enter the 8 or 13-digit EAN code."),
        # Temporarily disable strict EAN validation to allow bulk/product additions.
        # validators=[EanValidator()]
    )
    name = models.CharField(max_length=255, help_text="Description of this specific EAN variant (e.g., 'iPhone 13 128GB Blue')")
    product_model = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='eans')

    def __str__(self):
        return f'{self.name} (EAN: {self.ean})'

    class Meta:
        verbose_name = "EAN"
        verbose_name_plural = "EANs"


class MyProducts(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('company', 'product')

    def __str__(self):
        return f'MyProducts {self.id}'
