from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class FavoriteProceduresFolderHasProcedure(BaseModel):
    procedure = models.ForeignKey('Procedure', on_delete=models.CASCADE, db_column='procedure_code')
    favorite_procedures_folder = models.ForeignKey('FavoriteProceduresFolder', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('procedure', 'favorite_procedures_folder')
        db_table = get_snake_case_table_name(__qualname__) 