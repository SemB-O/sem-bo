from cbo.models._base import BaseModel
from django.db import models


class ProcedureHasRecord(BaseModel):
    competence_date = models.CharField(max_length=6, null=False)
    procedure = models.ForeignKey(
        'Procedure', on_delete=models.CASCADE, null=True, related_name='procedures_has_record')
    record = models.ForeignKey(
        'Record', on_delete=models.CASCADE, null=True, related_name='records_has_procedure')

    def __str__(self):
        return f'{self.record} => {self.procedure}'

    class Meta:
        indexes = [
            models.Index(fields=['procedure', 'record']),
        ]
        db_table = 'cbo_procedure_has_record'
