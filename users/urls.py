from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .views import HomeView, RegisterView, TemplateView

urlpatterns = [
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "register/",
        RegisterView.as_view(template_name="users/register.html"),
        name="register",
    ),
    path("home/", HomeView.as_view(template_name="users/home.html"), name="home"),
    path("profile/", views.profile, name="profile"),
    path("perfil/editar/", views.edit_profile, name="edit_profile"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="users/password_reset_form.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "terminos-de-uso/",
        TemplateView.as_view(template_name="users/legal/terms_of_use.html"),
        name="terms_of_use",
    ),
    path(
        "politica-de-privacidad/",
        TemplateView.as_view(template_name="users/legal/privacy_policy.html"),
        name="privacy_policy",
    ),
]
