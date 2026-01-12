from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class PlanHasPlanBenefit(BaseModel):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='plan_benefits')
    plan_benefit = models.ForeignKey(
        'PlanBenefit', related_name='plan_associations', on_delete=models.CASCADE)
    available = models.BooleanField(default=True)

    class Meta:
        db_table = get_snake_case_table_name(__qualname__)
        unique_together = ('plan', 'plan_benefit')  # Evita duplicatas
        indexes = [
            models.Index(fields=['plan', 'available']),
        ]

    def __str__(self):
        status = "✓" if self.available else "✗"
        return f"{status} {self.plan.name} - {self.plan_benefit.description}"
