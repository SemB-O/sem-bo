from cbo.models._base import BaseModel
from django.db import models
from .plan_has_plan_benift import PlanHasPlanBenefit
from cbo.camel_to_snake import get_snake_case_table_name

class Plan(BaseModel):
    name = models.CharField(max_length=150)
    max_occupations = models.PositiveIntegerField()
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    points = models.ManyToManyField(
        'PlanBenefit', related_name='plans', through='PlanHasPlanBenefit')

    def all_points(self):
        return PlanHasPlanBenefit.objects.filter(plan=self)

    def available_points(self):
        return self.points.filter(plan_benift__available=True)

    def unavailable_points(self):
        return self.points.filter(plan_benift__available=False)

    class Meta:
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return self.name
    
