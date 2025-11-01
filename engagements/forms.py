from django import forms

class AdoptionForm(forms.Form):
    """Adoption application form"""
    full_name = forms.CharField(
        max_length=200, 
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Tu nombre completo'
        })
    )
    phone = forms.CharField(
        max_length=20, 
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Tu número de teléfono'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Tu dirección completa'
        }), 
        label='Dirección'
    )
    city = forms.CharField(
        max_length=100, 
        label='Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Tu ciudad'
        })
    )
    occupation = forms.CharField(
        max_length=100, 
        label='Ocupación',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Tu ocupación'
        })
    )
    has_experience = forms.BooleanField(
        required=False, 
        label='¿Tienes experiencia con mascotas?',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
        })
    )
    has_other_pets = forms.BooleanField(
        required=False, 
        label='¿Tienes otras mascotas?',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
        })
    )
    other_pets_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Describe tus otras mascotas'
        }), 
        required=False,
        label='Describe tus otras mascotas'
    )
    housing_type = forms.CharField(
        max_length=100, 
        label='Tipo de vivienda',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Ej: Casa, Apartamento, Finca'
        })
    )
    has_outdoor_space = forms.BooleanField(
        required=False, 
        label='¿Tienes espacio al aire libre?',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
        })
    )
    reason_for_adoption = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Cuéntanos por qué deseas adoptar'
        }),
        label='¿Por qué deseas adoptar?'
    )

class SponsorshipForm(forms.Form):
    """Sponsorship application form"""
    full_name = forms.CharField(
        max_length=200, 
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
            'placeholder': 'Tu nombre completo'
        })
    )
    phone = forms.CharField(
        max_length=20, 
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
            'placeholder': 'Tu número de teléfono'
        })
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
            'placeholder': 'tu@email.com'
        })
    )
    monthly_contribution = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label='Aporte mensual (COP)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
            'placeholder': '50000',
            'min': '10000',
            'step': '1000'
        }),
        help_text='Mínimo $10,000 COP'
    )
    sponsorship_duration = forms.ChoiceField(
        choices=[
            ('1', '1 mes'),
            ('3', '3 meses'),
            ('6', '6 meses'),
            ('12', '1 año'),
            ('indefinido', 'Indefinido'),
        ],
        label='Duración del apadrinamiento',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
        })
    )
    reason_for_sponsorship = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
            'placeholder': 'Cuéntanos por qué deseas apadrinar a este animal'
        }),
        label='¿Por qué deseas apadrinar?'
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='Acepto recibir actualizaciones mensuales sobre el animal apadrinado',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500'
        })
    )