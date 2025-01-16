from django import forms
from django.urls import reverse_lazy


class RecordMedicalForm(forms.Form):
    cid_10 = forms.ChoiceField(
        choices=[],
        widget=forms.SelectMultiple(
            attrs={
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'cid_10',
                'data-placeholder': 'Selecione até 3 CIDs',
                'data-url': reverse_lazy('cid-autocomplete')
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
                'data-url': reverse_lazy('cid-autocomplete')
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
                'data-url': reverse_lazy('cid-autocomplete')
            }
        )
    )

    procedure = forms.ChoiceField(
        choices=[],
        widget=forms.SelectMultiple(
            attrs={
                'class': 'record-selects w-full px-4 py-2 rounded-md focus:outline-none',
                'id': 'procedure',
                'data-placeholder': 'Selecione até 3 procedimentos',
                'data-url': reverse_lazy('procedure-autocomplete')
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
                'data-url': reverse_lazy('procedure-autocomplete')
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
                'data-url': reverse_lazy('procedure-autocomplete')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        cid_options = kwargs.pop('cid_options', [])
        procedure_options = kwargs.pop('procedure_options', [])

        super().__init__(*args, **kwargs)

        self.fields['cid_10'].choices = cid_options
        self.fields['cid_initial'].choices = cid_options
        self.fields['cid_secundary'].choices = cid_options
        self.fields['procedure'].choices = procedure_options
        self.fields['procedure_principal'].choices = procedure_options
        self.fields['procedure_secundary'].choices = procedure_options