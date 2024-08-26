from cbo.models._base import BaseModel
from django.db import models


class PlanPointAvailability(BaseModel):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE)
    point = models.ForeignKey(
        'PlanPoint', related_name='plan_point', on_delete=models.CASCADE)
    available = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.plan.name} - {self.point.point_description}"

    class Meta:
        db_table = 'cbo_plan_point_availability'