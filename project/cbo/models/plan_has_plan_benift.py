from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class PlanHasPlanBenefit(BaseModel):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE)
    plan_benift = models.ForeignKey(
        'PlanBenefit', related_name='plan_point', on_delete=models.CASCADE)
    available = models.BooleanField(default=False)

    class Meta:
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return f"{self.plan.name} - {self.point.description}"
