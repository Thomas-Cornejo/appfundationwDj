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
    """
    Dashboard del perfil del usuario.
    Muestra sus animales adoptados y apadrinados.
    """
    from engagements.models import AnimalEngagement

    adoptions = AnimalEngagement.objects.filter(
        user=request.user, engagements_type="A", status="A"
    ).select_related("animal", "animal__breed", "animal__shelter")

    sponsorships = AnimalEngagement.objects.filter(
        user=request.user, engagements_type="S", status="A"
    ).select_related("animal", "animal__breed", "animal__shelter")

    sponsorships_with_care = []
    for sponsorship in sponsorships:
        if hasattr(sponsorship, "care_indicator"):
            sponsorships_with_care.append(
                {
                    "engagement": sponsorship,
                    "animal": sponsorship.animal,
                    "care_indicator": sponsorship.care_indicator,
                }
            )

    context = {
        "adoptions": adoptions,
        "sponsorships": sponsorships_with_care,
        "has_adoptions": adoptions.exists(),
        "has_sponsorships": len(sponsorships_with_care) > 0,
    }

    return render(request, "users/perfil.html", context)
