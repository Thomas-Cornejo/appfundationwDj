# engagements/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Adopciones
    path('adopt/<int:animal_id>/', views.adopt_animal, name='adopt_animal'),
    
    # Apadrinamientos
    path('sponsor/<int:animal_id>/', views.sponsor_animal, name='sponsor_animal'),  # 👈 NUEVA
    
    # Compartidas
    path('success/<int:engagement_id>/', views.engagement_success, name='engagement_success'),  # 👈 RENOMBRADA
    path('download-pdf/<int:engagement_id>/', views.download_pdf, name='download_pdf'),
]