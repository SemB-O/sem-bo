from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name

class PlanBenefit(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Nome do ícone ou emoji")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = get_snake_case_table_name(__qualname__)
        ordering = ['name']
        verbose_name = 'Plan Benefit'
        verbose_name_plural = 'Plan Benefits'

    def __str__(self):
        return self.name

    def get_plans_with_this_benefit(self):
        """Retorna todos os planos que têm este benefício disponível"""
        return self.plans.filter(
            plan_associations__available=True,
            plan_associations__plan_benefit=self
        )
