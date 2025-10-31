from django.urls import path
from . import views

urlpatterns = [
    path("adopt", views.animal_list, {"type": "adoption"}, name="adoption_list"),
    path(
        "sponsor/", views.animal_list, {"type": "sponsorship"}, name="sponsorhip_list"
    ),
    path("<int:animal_id>/", views.animal_detail, name="animal_detail"),
]
