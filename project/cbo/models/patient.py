from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class Patient(BaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = get_snake_case_table_name(__qualname__)    

    def __str__(self):
        return self.name