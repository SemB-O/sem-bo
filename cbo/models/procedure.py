from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class Procedure(BaseModel):
    procedure_code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=250, null=True)
    complexity_type = models.CharField(max_length=1, null=True)
    sex_type = models.CharField(max_length=1, null=True)
    maximum_execution_amount = models.IntegerField(null=True)
    stay_day_number = models.CharField(max_length=4, null=True)
    points_number = models.IntegerField(null=True)
    minimum_age_value = models.IntegerField(null=True)
    maximum_age_value = models.IntegerField(null=True)
    SH_value = models.IntegerField(null=True)
    SA_value = models.IntegerField(null=True)
    SP_value = models.IntegerField(null=True)
    stay_time_number = models.IntegerField(null=True)
    competence_date = models.CharField(max_length=6, null=True)

    def __str__(self):
        return getattr(self, 'name', '')

    class Meta:
        indexes = [
            models.Index(fields=['procedure_code', 'name']),
        ]
        db_table = get_snake_case_table_name(__qualname__) 

    def get_records_names(self):
        records = []
        if self.procedures_has_record.exists():
            for record in self.procedures_has_record.all():
                records.append(record.record.name)
            return records
        return "N/A"

    def is_favorite(self, user):
        from cbo.models.favorite_procedures_folder_has_procedure import FavoriteProceduresFolderHasProcedure
        return FavoriteProceduresFolderHasProcedure.objects.filter(favorite_procedures_folder__user=user, procedure=self).exists()
    
    def get_related_occupations(self, user):
        if user and user.occupations.exists():
            return self.procedures_has_occupation.filter(occupation__in=user.occupations.all())
        return []
    