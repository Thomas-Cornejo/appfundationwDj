from django.urls import path

from . import views, views_recharge

app_name = "gamifications"

urlpatterns = [
    path("animal/<int:animal_id>/", views.gamification_dashboard, name="dashboard"),
    path("animal/<int:animal_id>/feed/", views.feed_animal, name="feed"),
    path("animal/<int:animal_id>/clean/", views.clean_animal, name="clean"),
    path(
        "animal/<int:animal_id>/health/<int:history_id>/contribute/",
        views.contribute_health,
        name="contribute_health",
    ),
    path("animal/<int:animal_id>/status/", views.get_care_status, name="get_status"),
    path("recharge/", views_recharge.recharge_wallet, name="recharge_wallet"),
    path(
        "recharge/<int:animal_id>/",
        views_recharge.recharge_wallet,
        name="recharge_wallet_for_animal",
    ),
    path("recharge/create/", views_recharge.create_recharge, name="create_recharge"),
    path("recharge/callback/", views_recharge.recharge_callback, name="recharge_callback"),
    path("recharge/history/", views_recharge.recharge_history, name="recharge_history"),
    path("webhook/wompi/", views_recharge.wompi_webhook, name="wompi_webhook"),
]
