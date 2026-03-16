from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MissionSubmission


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class MissionSubmissionForm(forms.ModelForm):
    class Meta:
        model  = MissionSubmission
        fields = ['github_link', 'project_file', 'notes']
        widgets = {
            'github_link':  forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/you/project'}),
            'project_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes':        forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe what you built and how you approached the mission...'}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('github_link') and not cleaned.get('project_file'):
            raise forms.ValidationError('Please provide either a GitHub link or upload a project file.')
        return cleaned
