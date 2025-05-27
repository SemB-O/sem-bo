from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class ProcedureHasOccupation(BaseModel):
    competence_date = models.CharField(max_length=6, null=False)
    procedure = models.ForeignKey(
        'Procedure', on_delete=models.CASCADE, null=True, related_name='procedures_has_occupation')
    occupation = models.ForeignKey(
        'Occupation', on_delete=models.CASCADE, null=True, related_name='occupations_has_procedure')

    def __str__(self):
        return f'{self.occupation} => {self.procedure}'

    class Meta:
        indexes = [
            models.Index(fields=['procedure', 'occupation']),
        ]
        db_table = get_snake_case_table_name(__qualname__) 
