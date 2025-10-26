from django.urls import path
from . import views

urlpatterns = [
    path("adopt", views.animal_list, name="adoption_list"),
    path("<int:animal_id>/", views.animal_detail, name="animal_detail"),
]
