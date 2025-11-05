from django.urls import path
from . import views

app_name = 'gamifications'

urlpatterns = [
    path('animal/<int:animal_id>/', views.gamification_dashboard, name='dashboard'),
    
    path('animal/<int:animal_id>/feed/', views.feed_animal, name='feed'),
    path('animal/<int:animal_id>/clean/', views.clean_animal, name='clean'),
    path('animal/<int:animal_id>/health/<int:history_id>/contribute/', views.contribute_health, name='contribute_health'),
    
    path('animal/<int:animal_id>/status/', views.get_care_status, name='get_status'),
]
