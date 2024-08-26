from cbo.models._base import BaseModel
from django.db import models


class Patient(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name