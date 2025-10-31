from django.contrib.auth.views import LoginView, LogoutView
from .views import RegisterView, HomeView
from django.urls import path
from . import views

urlpatterns = [
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "register/",
        RegisterView.as_view(template_name="users/register.html"),
        name="register",
    ),
    path("home/", HomeView.as_view(template_name="users/home.html"), name="home"),
    path("perfil/", views.perfil, name="perfil"),
]