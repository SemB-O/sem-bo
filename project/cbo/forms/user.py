from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from ..models import User, Occupation, Plan
from collections.abc import Iterable
from datetime import date
import re
from django.core.exceptions import ValidationError
from django.db import transaction
from django import forms
from cbo.models import Occupation
from cbo.forms.fields import CPFField, DateOfBirthField


class PlanBasedOccupationField(forms.ModelMultipleChoiceField):
    def __init__(self, plan=None, *args, **kwargs):
        multiple = plan and getattr(plan, 'max_occupations', 1) > 1
        queryset = Occupation.objects.medical_only()

        label = "Ocupações" if multiple else "Ocupação"
        widget_attrs = {
            'class': 'select2 requiredField form-control',
            'id': 'occupation-select',
            'data-placeholder': (
                'Selecione uma ou mais ocupações de acordo com seu Plano' if multiple
                else 'Selecione uma ocupação de acordo com seu Plano'
            )
        }

        widget = (
            forms.SelectMultiple(attrs=widget_attrs) if multiple
            else forms.Select(attrs=widget_attrs)
        )

        super().__init__(queryset=queryset, label=label, widget=widget, *args, **kwargs)
        self.multiple = multiple

    def clean(self, value):
        value = value if self.multiple else [value]
        cleaned = super().clean(value)
        return list(cleaned)
    

DEFAULT_CLASS = 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2'


class LoginAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': DEFAULT_CLASS,
            'placeholder': 'seuemail@exemplo.com',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': DEFAULT_CLASS,
            'placeholder': '********',
            'autocomplete': 'current-password',
        })
    )

    class Meta:
        model = User
        fields = ['email', 'password']


    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not email or not password:
            return  

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.add_error('email', 'O email que você inseriu não está conectado a uma conta.')
            return

        user = authenticate(username=email, password=password)
        if user is None:
            self.add_error('password', 'A senha que você inseriu está incorreta.')
        else:
            cleaned_data['user'] = user  

        return cleaned_data
    

def validate_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        sum_val = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        digit = ((sum_val * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    return True

class UserRegisterForm(UserCreationForm):
    CPF = CPFField(
        widget=forms.TextInput(attrs={
            'class': f'requiredField {DEFAULT_CLASS}',
            'id': 'id_CPF',
            'placeholder': 'Digite seu CPF',
        })
    )
    date_of_birth = DateOfBirthField(
        widget=forms.DateInput(attrs={
            'class': f'requiredField {DEFAULT_CLASS}',
            'placeholder': 'Digite sua Data de nascimento',
            'type': 'date',
        }),
        label=User._meta.get_field('date_of_birth').verbose_name
    )

    class Meta:
        model = User
        fields = [
            'email', 
            'first_name', 
            'last_name', 
            'password1', 
            'password2', 
            'CPF', 
            'telephone', 
            'date_of_birth', 
            'occupational_registration', 
            'occupations'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'seuemail@exemplo.com',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite seu Nome',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite seu Sobrenome',
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite sua Senha',
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Confirme sua senha',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'id': 'id_telephone',
                'placeholder': 'Digite seu Celular',
            }),
            'occupational_registration': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite seu Registro ocupacional',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['occupations'] = PlanBasedOccupationField(plan=self.plan, required=True)

        self.fields['password1'].widget.attrs.update({
            'class': 'requiredField ' + DEFAULT_CLASS,
            'placeholder': 'Digite sua Senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'requiredField ' + DEFAULT_CLASS,
            'placeholder': 'Confirme sua Senha'
        })
                    
    def clean_occupations(self):
        occupations = self.cleaned_data.get('occupations')

        if isinstance(occupations, Iterable) and self.plan:
            max_allowed = self.plan.max_occupations
            if len(occupations) > max_allowed:
                raise forms.ValidationError(
                    f'Você pode selecionar no máximo {max_allowed} ocupações para este plano.'
                )

        return occupations

    # def clean_CPF(self):
    #     cpf = self.cleaned_data.get('CPF')
    #     if not validate_cpf(cpf):
    #         raise ValidationError("CPF inválido.")
    #     return cpf

    # def clean_date_of_birth(self):
    #     dob = self.cleaned_data.get('date_of_birth')
    #     if dob:
    #         today = date.today()
    #         age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    #         if age < 18:
    #             raise ValidationError("Você precisa ter pelo menos 18 anos.")
    #     return dob

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        first_name = self.cleaned_data.get('first_name', '') or ''
        last_name = self.cleaned_data.get('last_name', '') or ''
        email = self.cleaned_data.get('email', '') or ''

        if password1 and password2 and password1 != password2:
            raise ValidationError("As senhas não coincidem.")

        similar_data = [first_name.lower(), last_name.lower(), email.lower()]
        password_lower = password2.lower() if password2 else ''

        for value in similar_data:
            if value and value in password_lower:
                raise ValidationError("A senha não deve conter seu nome ou email.")

        return password2
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.plan = self.plan
        # user.is_active = False
        
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserEditForm(forms.ModelForm):  
    CPF = CPFField(
        widget=forms.TextInput(attrs={
            'class': f'requiredField {DEFAULT_CLASS}',
            'id': 'id_CPF',
            'placeholder': 'Digite seu CPF',
        })
    )
    date_of_birth = DateOfBirthField(
        widget=forms.DateInput(attrs={
            'class': f'requiredField {DEFAULT_CLASS}',
            'placeholder': 'Digite sua Data de nascimento',
            'type': 'date',
        }),
        label=User._meta.get_field('date_of_birth').verbose_name
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'CPF', 'telephone', 'date_of_birth', 'occupational_registration']
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md focus:outline-none', 'placeholder': 'Telefone'}),
            'occupational_registration': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md focus:outline-none', 'placeholder': 'Registro ocupacional'}),
        }


class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
            'placeholder': 'Digite seu email',
            'autocomplete': 'email',
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("O email fornecido não está associado a uma conta.")
        return email
    

class SetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label=_("Nova senha"),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
            'placeholder': 'Nova senha',
            'autocomplete': 'new-password',
        }),
        strip=False,
    )
    confirm_new_password = forms.CharField(
        label=_("Confirme a nova senha"),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
            'placeholder': 'Confirme a nova senha',
            'autocomplete': 'new-password',
        }),
        strip=False,
    )

    class Meta:
        model = get_user_model()
        fields = ['new_password', 'confirm_new_password']

    def clean_confirm_new_password(self):
        new_password = self.cleaned_data.get("new_password")
        confirm_new_password = self.cleaned_data.get("confirm_new_password")
        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValidationError(_("As senhas não correspondem."))
        return confirm_new_password

    def save(self, user, commit=True):
        user.set_password(self.cleaned_data["new_password"])
        if commit:
            user.save()
        return user

