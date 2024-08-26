from cbo.models._base import BaseModel
from django.db import models


class PlanPoint(BaseModel):
    point_description = models.CharField(max_length=255)

    def __str__(self):
        return self.point_description

    class Meta:
        db_table = 'cbo_plan_point'