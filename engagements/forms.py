from django import forms


class AdoptionForm(forms.Form):
    """Adoption application form"""

    full_name = forms.CharField(
        max_length=200,
        label="Nombre completo",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Tu nombre completo",
            }
        ),
    )
    phone = forms.CharField(
        max_length=20,
        label="Teléfono",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Tu número de teléfono",
            }
        ),
    )
    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Tu dirección completa",
            }
        ),
        label="Dirección",
    )
    city = forms.CharField(
        max_length=100,
        label="Ciudad",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Tu ciudad",
            }
        ),
    )
    occupation = forms.CharField(
        max_length=100,
        label="Ocupación",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Tu ocupación",
            }
        ),
    )
    has_experience = forms.BooleanField(
        required=False,
        label="¿Tienes experiencia con mascotas?",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            }
        ),
    )
    has_other_pets = forms.BooleanField(
        required=False,
        label="¿Tienes otras mascotas?",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            }
        ),
    )
    other_pets_description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Describe tus otras mascotas",
            }
        ),
        required=False,
        label="Describe tus otras mascotas",
    )
    housing_type = forms.CharField(
        max_length=100,
        label="Tipo de vivienda",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Ej: Casa, Apartamento, Finca",
            }
        ),
    )
    has_outdoor_space = forms.BooleanField(
        required=False,
        label="¿Tienes espacio al aire libre?",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            }
        ),
    )
    reason_for_adoption = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Cuéntanos por qué deseas adoptar",
            }
        ),
        label="¿Por qué deseas adoptar?",
    )


class SponsorshipForm(forms.Form):
    """Formulario de apadrinamiento virtual gamificado"""

    # Información Personal
    full_name = forms.CharField(
        max_length=200,
        label="Nombre completo",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                "placeholder": "Tu nombre completo",
            }
        ),
    )

    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                "placeholder": "tu@email.com",
            }
        ),
        help_text="Recibirás notificaciones y actualizaciones sobre tu mascota apadrinada",
    )

    phone = forms.CharField(
        max_length=20,
        label="Teléfono",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                "placeholder": "+57 300 123 4567",
            }
        ),
    )

    age_range = forms.ChoiceField(
        choices=[
            ("18-25", "18-25 años"),
            ("26-35", "26-35 años"),
            ("36-45", "36-45 años"),
            ("46-60", "46-60 años"),
            ("60+", "Más de 60 años"),
        ],
        label="Rango de edad",
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            }
        ),
    )

    occupation = forms.CharField(
        max_length=100,
        label="Ocupación",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                "placeholder": "Ej: Estudiante, Profesional, etc",
            }
        ),
        help_text="Esto nos ayuda a personalizar tu experiencia",
    )

    has_pet_experience = forms.ChoiceField(
        choices=[
            ("none", "Nunca he tenido mascotas"),
            ("some", "He tenido mascotas antes"),
            ("current", "Actualmente tengo mascotas"),
            ("professional", "Trabajo o he trabajado con animales"),
        ],
        label="Experiencia con animales",
        widget=forms.RadioSelect(
            attrs={"class": "text-purple-600 focus:ring-purple-500"}
        ),
    )

    reason_for_sponsorship = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                "placeholder": "Cuéntanos qué te motiva a apadrinar a este animal y cómo imaginas tu relación con él...",
            }
        ),
        label="¿Por qué quieres apadrinar a este animal?",
        help_text="Tu historia nos ayuda a crear una mejor experiencia de apadrinamiento",
    )

    interaction_goals = forms.MultipleChoiceField(
        choices=[
            ("daily_check", "Revisar su estado diariamente"),
            ("share_updates", "Compartir actualizaciones con amigos"),
            ("earn_badges", "Ganar insignias y logros"),
            ("donate_items", "Contribuir con items virtuales"),
            ("visit_shelter", "Visitar el refugio físicamente"),
            ("track_progress", "Seguir su progreso de salud"),
            ("participate_events", "Participar en eventos especiales"),
        ],
        label="¿Cómo planeas interactuar? (selecciona todas las que apliquen)",
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "text-purple-600 focus:ring-purple-500"}
        ),
        required=False,
    )

    availability_hours = forms.ChoiceField(
        choices=[
            ("casual", "Casual - Algunas veces al mes"),
            ("1-2", "Regular - 1-2 horas por semana"),
            ("3-5", "Activo - 3-5 horas por semana"),
            ("daily", "Muy activo - Un poco cada día"),
        ],
        label="¿Cuánto tiempo puedes dedicar?",
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            }
        ),
        help_text="Tiempo estimado de interacción semanal con tu mascota virtual",
    )

    motivation_level = forms.ChoiceField(
        choices=[
            ("casual", "🌟 Explorador - Quiero conocer el programa"),
            ("regular", "⭐⭐ Guardián - Me comprometo a cuidarlo regularmente"),
            ("dedicated", "⭐⭐⭐ Protector Elite - Seré un padrino muy dedicado"),
        ],
        label="Nivel de compromiso deseado",
        widget=forms.RadioSelect(
            attrs={"class": "text-purple-600 focus:ring-purple-500"}
        ),
        help_text="Puedes cambiar tu nivel más adelante según tu progreso",
    )

    preferred_activities = forms.MultipleChoiceField(
        choices=[
            ("feeding", "Alimentación virtual"),
            ("playing", "Juegos interactivos"),
            ("grooming", "Cuidado y aseo"),
            ("training", "Entrenamiento"),
            ("health", "Monitoreo de salud"),
            ("socialization", "Socialización con otros"),
        ],
        label="¿Qué actividades te interesan más?",
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "text-purple-600 focus:ring-purple-500"}
        ),
        required=False,
        help_text="Esto personalizará tu experiencia de juego",
    )

    notification_preferences = forms.ChoiceField(
        choices=[
            ("all", "Todas las actualizaciones"),
            ("important", "Solo actualizaciones importantes"),
            ("weekly", "Resumen semanal"),
            ("minimal", "Mínimo - Solo emergencias"),
        ],
        label="Preferencias de notificaciones",
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            }
        ),
    )

    willing_to_contribute = forms.ChoiceField(
        choices=[
            ("no", "Solo quiero participar virtualmente"),
            ("items", "Puedo donar items/suministros ocasionalmente"),
            ("monthly", "Me gustaría hacer una pequeña contribución mensual"),
        ],
        label="¿Te gustaría contribuir de alguna forma? (Opcional)",
        widget=forms.RadioSelect(
            attrs={"class": "text-purple-600 focus:ring-purple-500"}
        ),
        required=False,
        help_text="El apadrinamiento virtual es completamente gratuito. Cualquier contribución es opcional y bienvenida.",
    )

    accept_terms = forms.BooleanField(
        required=True,
        label="Acepto comprometerme a cuidar virtualmente de este animal, recibir notificaciones y seguir las reglas del programa de apadrinamiento",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            }
        ),
    )

    accept_data_usage = forms.BooleanField(
        required=True,
        label="Autorizo el uso de mis datos para personalizar mi experiencia de apadrinamiento",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            }
        ),
    )
