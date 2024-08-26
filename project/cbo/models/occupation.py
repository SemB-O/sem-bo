from cbo.models._base import BaseModel
from django.db import models


class Occupation(BaseModel):
    occupation_code = models.CharField(max_length=6, primary_key=True)
    name = models.CharField(max_length=150, null=True)

    class Meta:
        indexes = [
            models.Index(fields=[
                'occupation_code', 'name'
            ]),
        ]

    def __str__(self):
        return self.name