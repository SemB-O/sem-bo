from django import forms
from ..models import FavoriteProceduresFolder


class FavoriteProceduresFolderForm(forms.ModelForm):
    class Meta:
        model = FavoriteProceduresFolder
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')

        if FavoriteProceduresFolder.objects.filter(user=self.user, name=name).exists():
            raise forms.ValidationError('Você já criou uma pasta com esse nome.')

        return name

    def save(self, commit=True):
        self.instance.user = self.user  
        return super().save(commit=commit)