from cbo.models._base import BaseModel
from django.db import models


class Record(BaseModel):
    record_code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50, null=False)
    competence_date = models.CharField(max_length=6, null=False)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['record_code', 'name']),
        ]