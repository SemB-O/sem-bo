from django import forms
from ..models import FavoriteProceduresFolder


class FavoriteProceduresFolderForm(forms.ModelForm):
    class Meta:
        model = FavoriteProceduresFolder
        fields = ['name', 'description']

