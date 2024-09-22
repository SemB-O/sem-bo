from cbo.models._base import BaseModel
from cbo.models.user import User
from django.db import models


class Patient(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name