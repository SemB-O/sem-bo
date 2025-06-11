from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext 
from django.db import models
from cbo.models.managers import UserManager
import uuid
from cbo.models._base import BaseModel
from cbo.camel_to_snake import get_snake_case_table_name


class User(AbstractUser, BaseModel):
    first_name = models.CharField(max_length=150, verbose_name='Nome')
    last_name = models.CharField(max_length=150, verbose_name='Sobrenome')
    CPF = models.CharField(max_length=15, unique=True)
    email = models.EmailField(gettext("email address"), unique=True)
    telephone = models.CharField(max_length=15, verbose_name='Celular')
    date_of_birth = models.DateField(
        null=False, 
        blank=False,
        verbose_name='Data de Nascimento'    
    )
    occupational_registration = models.CharField(max_length=15, blank=True, null=True, verbose_name='Registro Ocupacional')
    occupations = models.ManyToManyField(
        'Occupation',
        through='UserHasOccupation',
        related_name='users',
        verbose_name='Ocupação'
    )
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
        db_table = get_snake_case_table_name(__qualname__) 
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def save(self, *args, **kwargs):
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt', 'argon2')):
            self.set_password(self.password)

        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.first_name + self.last_name

