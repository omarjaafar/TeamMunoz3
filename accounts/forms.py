from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile, CandidateSavedSearch


class ProfilePrivacyForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'show_headline',
            'show_location',
            'show_skills',
            'show_education',
            'show_projects',
            'show_experience',
            'show_links',
        ]
        widgets = {
            'show_headline': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_location': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_skills': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_education': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_projects': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_experience': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_links': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'show_headline': 'Show headline',
            'show_location': 'Show location',
            'show_skills': 'Show skills',
            'show_education': 'Show education',
            'show_projects': 'Show projects',
            'show_experience': 'Show work experience',
            'show_links': 'Show links/portfolio',
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['headline', 'location', 'skills', 'education', 'projects', 'experience', 'links', 'latitude', 'longitude',]
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CS student seeking SWE internships'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Comma or line separated (Python, Django, SQL...)'
            }),
            'education': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'School, degree, dates'
            }),
            'projects': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Past projects or notable work'
            }),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Company, role, achievements, dates'
            }),
            'links': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'LinkedIn, GitHub, portfolio URLs'
            }),

            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        
class CandidateSavedSearchForm(forms.ModelForm):
    class Meta:
        model = CandidateSavedSearch
        fields = ("name", "email_enabled")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Name (optional)"}),
            "email_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        if commit:
            user.save()
        return user