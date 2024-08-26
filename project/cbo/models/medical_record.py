from cbo.models._base import BaseModel
from django.db import models
from .patient import Patient


class MedicalRecord(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    record_name = models.CharField(max_length=255)
    pdf = models.FileField(upload_to='medical_records/')

    def __str__(self):
        return f"{self.record_name} - {self.patient.name}"