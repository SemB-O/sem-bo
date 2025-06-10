from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name
from django.db.models import Q
from functools import reduce
import operator


class OccupationManager(models.Manager):
    def medical_only(self):
        medical_keywords = [
            'Médico', 'Cirurgião', 'Enfermeiro', 'Dentista', 'Farmacêutico',
            'Fisioterapeuta', 'Nutricionista', 'Psicólogo', 'Psiquiatra', 'Radiologista',
            'Oncologista', 'Cardiologista', 'Ginecologista', 'Pediatra', 'Ortopedista',
            'Fonoaudiólogo', 'Terapeuta', 'Ortoptista', 'Psicomotricista', 'Saúde', 'Neuro'
        ]

        query = reduce(operator.or_, (Q(name__icontains=kw) for kw in medical_keywords))
        return self.filter(query)


class Occupation(BaseModel):
    occupation_code = models.CharField(max_length=6, primary_key=True)
    name = models.CharField(max_length=150, null=True)

    objects = OccupationManager() 

    class Meta:
        indexes = [
            models.Index(fields=[
                'occupation_code', 'name'
            ]),
        ]
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return self.name