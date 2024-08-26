from cbo.models._base import BaseModel
from django.db import models


class FavoriteFolder(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'name')
        db_table = 'cbo_favorite_folder'

    def __str__(self):
        return self.name