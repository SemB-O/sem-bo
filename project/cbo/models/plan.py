from cbo.models._base import BaseModel
from django.db import models


class Plan(BaseModel):
    name = models.CharField(max_length=150)
    max_occupations = models.PositiveIntegerField()
    description = models.TextField()
    points = models.ManyToManyField(
        'PlanPoint', related_name='plans', through='PlanPointAvailability')

    def all_points(self):
        return self.points.all()

    def available_points(self):
        return self.points.filter(plan_point__available=True)

    def unavailable_points(self):
        return self.points.filter(plan_point__available=False)

    def __str__(self):
        return self.name
    
