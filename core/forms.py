from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import AlertPreference


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Choose a username"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"autocomplete": "username"})
        self.fields["email"].widget.attrs.update({"autocomplete": "email"})
        self.fields["password1"].widget.attrs.update(
            {"placeholder": "Create a password", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "Repeat password", "autocomplete": "new-password"}
        )


class WeatherSearchForm(forms.Form):
    city = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"placeholder": "Search city"}))

    def clean_city(self):
        value = (self.cleaned_data.get("city") or "").strip()
        if len(value) < 2:
            raise forms.ValidationError("Please enter a valid city name.")
        if not all(ch.isalpha() or ch.isspace() or ch in "-'," for ch in value):
            raise forms.ValidationError("City name contains invalid characters.")
        return value


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "is_staff", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
        }


class AlertPreferenceForm(forms.ModelForm):
    class Meta:
        model = AlertPreference
        fields = ("city", "country", "temperature_threshold", "condition_alerts", "email_alerts")
        widgets = {
            "city": forms.TextInput(attrs={"placeholder": "City for alert"}),
            "country": forms.TextInput(attrs={"placeholder": "Country (optional)"}),
            "temperature_threshold": forms.NumberInput(attrs={"placeholder": "Temp threshold (deg C)"}),
        }


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Username", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Password", "autocomplete": "current-password"}
        )
