from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from ..models import User, Occupation, Plan


class LoginAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none border-gray-300',
            'placeholder': 'Digite seu email',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none border-gray-300',
            'placeholder': 'Digite sua senha',
            'autocomplete': 'current-password',
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['email', 'password']


class UserRegisterForm(UserCreationForm):
    def filter_occupations(self):
        occupations = Occupation.objects.all()
        
        medical_keywords = [
            'Médico', 'Cirurgião', 'Enfermeiro', 'Dentista', 'Farmacêutico',
            'Fisioterapeuta', 'Nutricionista', 'Psicólogo', 'Psiquiatra', 'Radiologista',
            'Oncologista', 'Cardiologista', 'Ginecologista', 'Pediatra', 'Ortopedista',
            'Fonoaudiólogo', 'Terapeuta', 'Ortoptista', 'Psicomotricista', 'Saúde', 'Neuro'
        ]
        
        medic_occupations = occupations.none()

        for keyword in medical_keywords:
            medic_occupations |= occupations.filter(name__icontains=keyword)
        
        return medic_occupations

    plan = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        widget=forms.Select(
            attrs={
                'class': 'requiredField plan-select w-full px-4 py-2 rounded-md focus:outline-none',
                'data-placeholder': 'Selecione seu Plano'
            }
        ),
    )

    occupation = forms.ModelMultipleChoiceField(
        queryset=filter_occupations(None), 
        widget=forms.SelectMultiple(
            attrs={
                'class': 'requiredField occupation-select w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'occupation-select',
                'data-placeholder': 'Selecione uma ou mais ocupações de acordo com seu Plano'
            },
        ),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2', 'CPF', 'telephone', 'date_of_birth', 'occupational_registration', 'occupation', 'plan']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Email',
                'required': 'false'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Nome',
                'required': 'false'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Sobrenome',
                'required': 'false'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite sua Senha',
                'required': 'false'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Confirme sua senha',
                'required': 'false'
            }),
            'CPF': forms.TextInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'id_CPF',
                'placeholder': 'Digite seu CPF',
                'required': 'false'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'id_telephone',
                'placeholder': 'Digite seu Telefone',
                'required': 'false'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite sua Data de nascimento',
                'type': 'date',
                'required': 'false'
            }),
            'occupational_registration': forms.TextInput(attrs={
                'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Registro ocupacional',
                'required': 'false'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
            'placeholder': 'Digite sua Senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'requiredField w-full px-4 py-2 rounded-md focus:outline-none',
            'placeholder': 'Confirme sua Senha'
        })

    def clean(self):
        cleaned_data = super().clean()
        plan = cleaned_data.get('plan')
        occupations = cleaned_data.get('occupation')

        if plan and occupations:
            if plan.name == 'Plano Essencial' and len(occupations) > 1:
                raise ValidationError('O Plano Essencial permite selecionar apenas uma ocupação.')
            elif plan.name == 'Plano Essencial +' and len(occupations) > 3:
                raise ValidationError('O Plano Essencial + permite selecionar até 3 ocupações.')

        return cleaned_data


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

