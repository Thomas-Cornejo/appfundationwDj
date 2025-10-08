from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.contrib.auth.decorators import login_required


class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")


class HomeView(TemplateView):
    template_name = "users/home.html"

@login_required
def perfil(request):
    return render(request, "users/perfil.html")
