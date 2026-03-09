from django import forms
from django.contrib.auth.hashers import make_password
from .models import CustomerUser


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password'
        }),
        label="Password"
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label="Confirm Password"
    )

    class Meta:
        model = CustomerUser
        fields = ['username', 'email', 'full_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or email'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerUser
        fields = ['full_name', 'email', 'profile_image', 'bio', 'phone', 'gender', 'dob', 'country']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }

from django import forms
from .models import HealthRecord
from django.utils import timezone

class HealthRecordForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now
    )

    class Meta:
        model = HealthRecord
        fields = ['date', 'weight', 'systolic_bp', 'diastolic_bp', 'sugar_level', 'sleep_hours', 'exercise_minutes', 'stress_level']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'systolic_bp': forms.NumberInput(attrs={'class': 'form-control'}),
            'diastolic_bp': forms.NumberInput(attrs={'class': 'form-control'}),
            'sugar_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'sleep_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'exercise_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'stress_level': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class HealthRecordImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label="Upload Excel/CSV"
    )