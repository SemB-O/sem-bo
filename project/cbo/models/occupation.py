from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class Occupation(BaseModel):
    occupation_code = models.CharField(max_length=6, primary_key=True)
    name = models.CharField(max_length=150, null=True)

    class Meta:
        indexes = [
            models.Index(fields=[
                'occupation_code', 'name'
            ]),
        ]
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return self.name