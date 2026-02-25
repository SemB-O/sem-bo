from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class Cid(BaseModel):
    cid_code = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=100, null=False)
    grievance_type = models.CharField(max_length=1, null=False)
    sex_type = models.CharField(max_length=1, null=False)
    stadium_stype = models.CharField(max_length=1, null=False)
    irradiated_fields_value = models.IntegerField(null=False)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['cid_code', 'name']),
        ]
        db_table = get_snake_case_table_name(__qualname__) 