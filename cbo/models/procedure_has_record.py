from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class ProcedureHasRecord(BaseModel):
    competence_date = models.CharField(max_length=6, null=False)
    procedure = models.ForeignKey(
        'Procedure', on_delete=models.CASCADE, null=True, related_name='procedures_has_record', db_column='procedure_code'
    )
    record = models.ForeignKey(
        'Record', on_delete=models.CASCADE, null=True, related_name='records_has_procedure', db_column='record_code'
    )   

    def __str__(self):
        return f'{self.record} => {self.procedure}'

    class Meta:
        indexes = [
            models.Index(fields=['procedure', 'record']),
        ]
        db_table = get_snake_case_table_name(__qualname__) 