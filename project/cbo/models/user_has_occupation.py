from django.db import models
from cbo.models._base import BaseModel
from cbo.camel_to_snake import get_snake_case_table_name


class UserHasOccupation(BaseModel):
    occupation = models.ForeignKey(
        'Occupation',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = get_snake_case_table_name(__qualname__) 
