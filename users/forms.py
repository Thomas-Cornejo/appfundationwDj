from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    phone_number = PhoneNumberField(
        label="Teléfono",
        region="CO",
        widget=RegionalPhoneNumberWidget(
            attrs={
                "class": "block w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Ej: 3001234567",
            }
        ),
        required=False,
    )
    accepted_data_policy = forms.BooleanField(
        required=True,
        label="",
        error_messages={"required": "Debes de aceptar los terminos y condiciones para continuar."},
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "phone_number",
            "password1",
            "password2",
            "accepted_data_policy",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ["email", "phone_number"]:
            if field in self.fields:
                self.fields[field].required = True

        if "password1" in self.fields:
            self.fields["password1"].help_text = None
        if "password2" in self.fields:
            self.fields["password2"].help_text = None

    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get("email")
        if email and CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email
