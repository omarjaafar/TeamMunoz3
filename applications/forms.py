from django import forms
from .models import Application


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status"]

    status = forms.ChoiceField(
        choices=Application.Status.choices,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
