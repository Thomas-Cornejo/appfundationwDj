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
    
    reason_for_sponsorship = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
            'placeholder': 'Cuéntanos por qué deseas apadrinar a este animal y cómo planeas interactuar con él'
        }),
        label='¿Por qué deseas apadrinar?',
        help_text='El apadrinamiento te permitirá cuidar virtualmente del animal a través de nuestro sistema gamificado'
    )
    availability_hours = forms.ChoiceField(
        choices=[
            ('1-2', '1-2 horas por semana'),
            ('3-5', '3-5 horas por semana'),
            ('6-10', '6-10 horas por semana'),
            ('10+', 'Más de 10 horas por semana'),
        ],
        label='¿Cuánto tiempo puedes dedicar?',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
        }),
        help_text='Tiempo estimado que dedicarás a interactuar con el animal en el sistema'
    )
    motivation_level = forms.ChoiceField(
        choices=[
            ('casual', 'Casual - Quiero ayudar ocasionalmente'),
            ('regular', 'Regular - Me comprometo a visitas frecuentes'),
            ('dedicated', 'Dedicado - Quiero ser un padrino muy activo'),
        ],
        label='Nivel de compromiso',
        widget=forms.RadioSelect(attrs={
            'class': 'text-purple-600 focus:ring-purple-500'
        })
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='Acepto recibir notificaciones sobre el estado del animal y comprometerme a cuidar de él virtualmente',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500'
        })
    )