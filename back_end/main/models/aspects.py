from django.db import models
import logging
logger = logging.getLogger(__name__)


class Aspect(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    def __str__(self):
        return self.name

class Subaspect(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
