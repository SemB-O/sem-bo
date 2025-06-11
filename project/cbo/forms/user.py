from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from ..models import User, Occupation, Plan
from collections.abc import Iterable

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
    
class UserRegisterForm(UserCreationForm):

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
                'required': 'false'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite seu Nome',
                'required': 'false'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite seu Sobrenome',
                'required': 'false'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite sua Senha',
                'required': 'false'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Confirme sua senha',
                'required': 'false'
            }),
            'CPF': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'id': 'id_CPF',
                'placeholder': 'Digite seu CPF',
                'required': 'false'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'id': 'id_telephone',
                'placeholder': 'Digite seu Celular',
                'required': 'false'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite sua Data de nascimento',
                'type': 'date',
                'required': 'false'
            }),
            'occupational_registration': forms.TextInput(attrs={
                'class': 'requiredField ' + DEFAULT_CLASS,
                'placeholder': 'Digite seu Registro ocupacional',
                'required': 'false'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.set_occupations_field_based_on_plan(self.plan)        

        self.fields['password1'].widget.attrs.update({
            'class': 'requiredField ' + DEFAULT_CLASS,
            'placeholder': 'Digite sua Senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'requiredField ' + DEFAULT_CLASS,
            'placeholder': 'Confirme sua Senha'
        })

    def set_occupations_field_based_on_plan(self, plan):
        occupation_queryset = Occupation.objects.medical_only()

        if plan and getattr(plan, 'max_occupations', 1) > 1:
            self.fields['occupations'] = forms.ModelMultipleChoiceField(
                queryset=occupation_queryset,
                required=True,
                widget=forms.SelectMultiple(attrs={
                    'class': f'select2 requiredField {DEFAULT_CLASS}',
                    'id': 'occupation-select',
                    'data-placeholder': 'Selecione uma ou mais ocupações de acordo com seu Plano',
                })
            )
        else:
            self.fields['occupations'] = forms.ModelChoiceField(
                queryset=occupation_queryset,
                required=True,
                widget=forms.Select(attrs={
                    'class': f'select2 requiredField {DEFAULT_CLASS}',
                    'id': 'occupation-select',
                    'data-placeholder': 'Selecione uma ocupação de acordo com seu Plano',
                })
            )

    def clean_occupations(self):
        occupations = self.cleaned_data.get('occupations')

        if isinstance(occupations, Iterable) and self.plan:
            max_allowed = self.plan.max_occupations
            if len(occupations) > max_allowed:
                raise forms.ValidationError(
                    f'Você pode selecionar no máximo {max_allowed} ocupações para este plano.'
                )

        return occupations

    def save(self, commit=True):
        user = super().save(commit=False)
        user.plan = self.plan
        # user.is_active = False
        
        if commit:
            user.save()

            occupations = self.cleaned_data.get('occupation')
            for occupation in occupations:
                user.occupations.add(occupation)

            self.save_m2m()
        return user

class UserEditForm(forms.ModelForm):  
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'CPF', 'telephone', 'date_of_birth', 'occupational_registration']
        widgets = {
            'CPF': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md focus:outline-none', 'placeholder': 'CPF'}),
            'telephone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md focus:outline-none', 'placeholder': 'Telefone'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'w-full px-4 py-2 rounded-md focus:outline-none', 'placeholder': 'Data de nascimento'}),
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

