from django.db import models
from cbo.models._base import BaseModel
from cbo.camel_to_snake import get_snake_case_table_name


class Description(BaseModel):
    procedure = models.ForeignKey('Procedure', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    competence_date = models.CharField(max_length=6, null=True)

    class Meta:
        verbose_name = 'Description'
        verbose_name_plural = 'Descriptions'
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return self.procedure.name