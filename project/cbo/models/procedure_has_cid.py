from cbo.models._base import BaseModel
from django.db import models


class ProcedureHasCid(BaseModel):
    st_principal = models.CharField(max_length=4, null=False)
    competence_date = models.CharField(max_length=6, null=False)
    procedure = models.ForeignKey(
        'Procedure', on_delete=models.CASCADE, null=True, related_name='procedures_has_cid')
    cid = models.ForeignKey('Cid', on_delete=models.CASCADE,
                            null=True, related_name='cids_has_procedure')

    def __str__(self):
        return f'{self.cid} => {self.procedure}'

    class Meta:
        indexes = [
            models.Index(fields=['procedure', 'cid']),
        ]
        db_table = 'cbo_procedure_has_cid'