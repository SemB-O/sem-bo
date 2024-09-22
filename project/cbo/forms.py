from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Occupation, Plan
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth import get_user_model
from .models import FavoriteFolder, Procedure, Cid
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy


class EmailAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        return self.cleaned_data['username']

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
                'class': 'plan-select w-full px-4 py-2 rounded-md focus:outline-none',
                'data-placeholder': 'Selecione seu Plano'
            }
        ),
    )

    occupation = forms.ModelMultipleChoiceField(
        queryset=filter_occupations(None), 
        widget=forms.SelectMultiple(
            attrs={
                'class': 'occupation-select w-full px-4 py-2 rounded-md focus:outline-none',
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
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Email',
                'required': 'false'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Nome',
                'required': 'false'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Sobrenome',
                'required': 'false'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite sua Senha',
                'required': 'false'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Confirme sua senha',
                'required': 'false'
            }),
            'CPF': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'id_CPF',
                'placeholder': 'Digite seu CPF',
                'required': 'false'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'id_telephone',
                'placeholder': 'Digite seu Telefone',
                'required': 'false'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite sua Data de nascimento',
                'type': 'date',
                'required': 'false'
            }),
            'occupational_registration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
                'placeholder': 'Digite seu Registro ocupacional',
                'required': 'false'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
            'placeholder': 'Digite sua Senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 rounded-md focus:outline-none',
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
    email = forms.EmailField(label='Email')

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("O email fornecido não está associado a uma conta.")
        return email
    

class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = get_user_model()
        fields = ['new_password1', 'new_password2']


class FavoriteFolderForm(forms.ModelForm):
    class Meta:
        model = FavoriteFolder
        fields = ['name', 'description']


class RecordMedicalForm(forms.Form):
    cid_10 = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(
            attrs={
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'cid_10',
                'data-placeholder': 'Selecione até 3 CIDs',
            },
        ),
    )

    cid_initial = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={
                'id': 'cid_initial',
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'data-placeholder': 'Selecione o CID',
            }
        )
    )

    cid_secundary = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={
                'id': 'cid_secundary',
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'data-placeholder': 'Selecione o CID',
            }
        )
    )

    procedure = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(
            attrs={
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'procedure',
                'data-placeholder': 'Selecione até 3 procedimentos',
            },
        ),
    )

    procedure_principal = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={
                'id': 'procedure_principal',
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'data-placeholder': 'Selecione o procedimento',
            }
        )
    )

    procedure_secundary = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={
                'id': 'procedure_secundary',
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'data-placeholder': 'Selecione o procedimento',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ResumoAltaForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=100)
    prontuario = forms.CharField(label="Prontuário", max_length=100)
    idade = forms.IntegerField(label="Idade")
    internacao = forms.DateField(label="Data de Internação", widget=forms.TextInput(attrs={'type': 'date'}))
    alta = forms.DateField(label="Data de Alta", widget=forms.TextInput(attrs={'type': 'date'}))
    motivo_internacao = forms.CharField(label="Motivo da Internação", widget=forms.Textarea)
    resumo_internacao = forms.CharField(label="Resumo da Internação", widget=forms.Textarea)
    cirurgia = forms.CharField(label="Cirurgia", required=False, widget=forms.Textarea)
    exames = forms.CharField(label="Resultados dos Principais Exames", widget=forms.Textarea)
    medicacoes = forms.CharField(label="Medicações e Recomendações", widget=forms.Textarea)
    diagnostico_alta = forms.CharField(label="Diagnóstico da Alta", widget=forms.Textarea)
