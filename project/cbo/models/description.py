from django.db import models
from cbo.models._base import BaseModel


class Description(BaseModel):
    procedure = models.ForeignKey('Procedure', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    competence_date = models.CharField(max_length=6, null=True)

    class Meta:
        db_table = 'cbo_description'
        verbose_name = 'Description'
        verbose_name_plural = 'Descriptions'

    def __str__(self):
        return self.procedure.name