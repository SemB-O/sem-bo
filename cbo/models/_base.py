from django.db import models
import re


class BaseModel(models.Model):

    class Meta:
        abstract = True
