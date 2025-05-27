from cbo.models._base import BaseModel
from django.db import models
from cbo.camel_to_snake import get_snake_case_table_name


class MedicalRecord(BaseModel):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    record_name = models.CharField(max_length=255)
    pdf = models.FileField(upload_to='medical_records/')

    class Meta:
        db_table = get_snake_case_table_name(__qualname__) 

    def __str__(self):
        return f"{self.record_name} - {self.patient.name}"