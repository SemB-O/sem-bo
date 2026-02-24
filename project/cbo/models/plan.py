from cbo.models._base import BaseModel
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from cbo.camel_to_snake import get_snake_case_table_name

class Plan(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    max_occupations = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Número máximo de ocupações permitidas neste plano"
    )
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True)
    benefits = models.ManyToManyField(
        'PlanBenefit', 
        related_name='plans', 
        through='PlanHasPlanBenefit',
        blank=True
    )

    class Meta:
        db_table = get_snake_case_table_name(__qualname__)
        ordering = ['price', 'name']
        indexes = [
            models.Index(fields=['is_active', 'price']),
        ]

    def __str__(self):
        return f"{self.name} (R$ {self.price})"

    # Métodos melhorados e mais eficientes
    def get_all_benefit_associations(self):
        """Retorna todas as associações de benefícios (QuerySet)"""
        return self.plan_benefits.select_related('plan_benefit').all()

    def get_available_benefits(self):
        """Retorna apenas os benefícios disponíveis (QuerySet otimizado)"""
        return self.benefits.filter(
            plan_associations__available=True,
            plan_associations__plan=self
        )

    def get_unavailable_benefits(self):
        """Retorna apenas os benefícios indisponíveis (QuerySet otimizado)"""
        return self.benefits.filter(
            plan_associations__available=False,
            plan_associations__plan=self
        )

    def has_benefit(self, benefit):
        """Verifica se o plano tem um benefício específico e está disponível"""
        return self.plan_benefits.filter(
            plan_benefit=benefit,
            available=True
        ).exists()

    def add_benefit(self, benefit, available=True):
        """Adiciona um benefício ao plano de forma segura"""
        from .plan_has_plan_benift import PlanHasPlanBenefit
        association, created = PlanHasPlanBenefit.objects.get_or_create(
            plan=self,
            plan_benefit=benefit,
            defaults={'available': available}
        )
        if not created and association.available != available:
            association.available = available
            association.save()
        return association

    def remove_benefit(self, benefit):
        """Remove um benefício do plano"""
        self.plan_benefits.filter(plan_benefit=benefit).delete()

    def toggle_benefit_availability(self, benefit):
        """Alterna a disponibilidade de um benefício"""
        association = self.plan_benefits.get(plan_benefit=benefit)
        association.available = not association.available
        association.save()
        return association.available
    
