from django import forms
from django.contrib.auth.forms import UserCreationForm
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

    class Meta:
        model = CustomUser
        fields = ("username", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ["email", "phone_number"]:
            if field in self.fields:
                self.fields[field].required = True
