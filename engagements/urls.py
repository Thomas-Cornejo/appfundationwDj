from django.urls import path

from . import views

urlpatterns = [
    path("adopt/<int:animal_id>/", views.adopt_animal, name="adopt_animal"),
    path("sponsor/<int:animal_id>/", views.sponsor_animal, name="sponsor_animal"),
    path(
        "success/<int:engagement_id>/",
        views.engagement_success,
        name="engagement_success",
    ),
    path("download-pdf/<int:engagement_id>/", views.download_pdf, name="download_pdf"),
    path("visits/<int:engagement_id>/", views.animal_visits, name="animal_visits"),
]
