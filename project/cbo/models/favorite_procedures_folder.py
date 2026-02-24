from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class FavoriteProceduresFolder(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'name')
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return self.name