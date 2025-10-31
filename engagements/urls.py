from django.urls import path
from . import views

urlpatterns = [
    path('adopt/<int:animal_id>/', views.adopt_animal, name='adopt_animal'),
    path('adoption-success/<int:engagement_id>/', views.adoption_success, name='adoption_success'),
    path('download-pdf/<int:engagement_id>/', views.download_pdf, name='download_pdf'),
]
