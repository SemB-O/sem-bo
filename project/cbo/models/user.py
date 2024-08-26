from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext 
from django.db import models
from cbo.models.managers import UserManager
from django.core.exceptions import ValidationError
import uuid
from cbo.models._base import BaseModel


class User(AbstractUser, BaseModel):
    CPF = models.CharField(max_length=15)
    email = models.EmailField(gettext("email address"), unique=True)
    telephone = models.CharField(max_length=15)
    date_of_birth = models.DateField(
        null=False, blank=False, default='2000-01-01')
    occupational_registration = models.CharField(max_length=15)
    occupations = models.ManyToManyField('Occupation', related_name='users')
    plan = models.ForeignKey(
        'Plan', on_delete=models.SET_NULL, null=True, related_name='users')
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(
        default=uuid.uuid4, editable=False)
    
    username = None
    date_joined = None

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [
            models.Index(fields=['first_name', 'occupational_registration']),
        ]

    def save(self, *args, **kwargs):
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt', 'argon2')):
            self.set_password(self.password)

        super(User, self).save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.username:
            raise ValidationError("Username não é permitido.")

        # if self.date_of_birth > timezone.now().date():
        #     raise ValidationError("A data de nascimento não pode ser maior que o dia atual.")

    def __str__(self):
        return self.first_name + self.last_name

