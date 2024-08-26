from cbo.models._base import BaseModel
from django.db import models


class FavoriteProcedure(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    procedure = models.ForeignKey('Procedure', on_delete=models.CASCADE)
    folder = models.ForeignKey('FavoriteFolder', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'procedure', 'folder')
        db_table = 'cbo_favorite_procedure'