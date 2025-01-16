from django import forms
from ..models import FavoriteFolder


class FavoriteFolderForm(forms.ModelForm):
    class Meta:
        model = FavoriteFolder
        fields = ['name', 'description']

