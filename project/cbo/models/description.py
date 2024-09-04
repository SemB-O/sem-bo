from django.db import models
from cbo.models._base import BaseModel  # Presumindo que você tenha um modelo base que estende os modelos do Django

class Description(BaseModel):
    procedure = models.ForeignKey('Procedure', on_delete=models.CASCADE)
    description = models.TextField()
    competence_date = models.CharField(max_length=6, null=True)

    class Meta:
        db_table = 'cbo_description'  # Nome da tabela no banco de dados
        verbose_name = 'Description'
        verbose_name_plural = 'Descriptions'
