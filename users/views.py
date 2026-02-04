from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView

from .forms import CustomUserCreationForm
from .models import CustomUser


class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")


class HomeView(TemplateView):
    template_name = "users/home.html"


@login_required
def profile(request):
    """
    Dashboard del profile del usuario.
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
        "adoptions": adoptions if adoptions.exists() else [],
        "sponsorships": sponsorships_with_care if sponsorships_with_care else [],
        "has_adoptions": adoptions.exists(),
        "has_sponsorships": len(sponsorships_with_care) > 0,
        "user": request.user,
    }

    return render(request, "users/profile.html", context)


@login_required
def edit_profile(request):
    """
    Permite al usuario editar su profile.
    """
    if request.method == "POST":
        user = request.user

        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.address = request.POST.get("address", user.address)

        try:
            user.full_clean()
            user.save()
            messages.success(request, "profile actualizado correctamente")
            return redirect("profile")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {str(e)}")

    return render(request, "users/edit_profile.html", {"user": request.user})


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get("accepted_data_policy"):
                user.accepted_data_policy = True
                user.accepted_data_policy_at = timezone.now()
            user.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", {"form": form})
