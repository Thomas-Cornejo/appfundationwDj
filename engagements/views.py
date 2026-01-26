from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from animals.models import Animal

from .forms import AdoptionForm, SponsorshipForm
from .models import AnimalEngagement, Visit
from .utils import generate_adoption_pdf, generate_sponsorship_pdf


@login_required
def adopt_animal(request, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    user = request.user

    existing = AnimalEngagement.objects.filter(
        user=user, animal=animal, engagements_type="A", status__in=["P", "A"]
    ).first()

    if existing:
        return render(
            request,
            "engagements/already_applied.html",
            {"engagement": existing, "animal": animal, "engagement_type": "adopción"},
        )

    if request.method == "POST":
        form = AdoptionForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            engagement = AnimalEngagement.objects.create(
                user=user,
                animal=animal,
                engagements_type="A",
                status="P",
                form_data=form_data,
            )

            pdf_buffer = generate_adoption_pdf(engagement, form_data)

            filename = f"Solicitud_Adopcion_{user.username}_para_{animal.name}.pdf"
            filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

            engagement.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)

            messages.success(request, f"¡Solicitud de adopción enviada para {animal.name}!")
            return redirect("engagement_success", engagement_id=engagement.id)
    else:
        form = AdoptionForm()

    return render(request, "engagements/adoption_form.html", {"form": form, "animal": animal})


@login_required
def sponsor_animal(request, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    user = request.user

    existing = AnimalEngagement.objects.filter(
        user=user, animal=animal, engagements_type="S", status__in=["P", "A"]
    ).first()

    if existing:
        return render(
            request,
            "engagements/already_applied.html",
            {
                "engagement": existing,
                "animal": animal,
                "engagement_type": "apadrinamiento",
            },
        )

    if request.method == "POST":
        form = SponsorshipForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            engagement = AnimalEngagement.objects.create(
                user=user,
                animal=animal,
                engagements_type="S",
                status="P",
                form_data=form_data,
            )

            pdf_buffer = generate_sponsorship_pdf(engagement, form_data)

            filename = f"Solicitud_Apadrinamiento_{user.username}_para_{animal.name}.pdf"
            filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

            engagement.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)

            messages.success(request, f"¡Solicitud de apadrinamiento enviada para {animal.name}!")
            return redirect("engagement_success", engagement_id=engagement.id)
    else:
        form = SponsorshipForm()

    return render(request, "engagements/sponsorship_form.html", {"form": form, "animal": animal})


@login_required
def engagement_success(request, engagement_id):
    """Vista unificada de éxito para adopciones y apadrinamientos"""
    engagement = get_object_or_404(AnimalEngagement, pk=engagement_id, user=request.user)

    engagement_type = engagement.get_engagements_type_display()

    return render(
        request,
        "engagements/engagement_success.html",
        {
            "engagement": engagement,
            "engagement_type": engagement_type,
            "animal": engagement.animal,
        },
    )


@login_required
def download_pdf(request, engagement_id):
    """Vista para descargar/ver el PDF desde Cloudinary"""
    engagement = get_object_or_404(AnimalEngagement, pk=engagement_id)

    if not (request.user == engagement.user or request.user.is_staff):
        raise Http404("No tienes permiso para ver este archivo")

    if not engagement.pdf_file:
        raise Http404("No hay PDF disponible")

    return redirect(engagement.pdf_file.url)


@login_required
def animal_visits(request, engagement_id):
    """
    Vista para mostrar todas las visitas de un animal adoptado.
    Solo el usuario adoptante puede ver sus visitas.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        pk=engagement_id,
        user=request.user,
        engagements_type="A",  # Solo adopciones
        status="A",  # Solo aprobadas
    )

    # Obtener visitas programadas (futuras y no completadas)
    from django.utils import timezone

    scheduled_visits = Visit.objects.filter(
        animal_engagement=engagement, completed=False, visit_date__gte=timezone.now()
    ).order_by("visit_date")

    # Obtener visitas vencidas (pasadas y no completadas)
    overdue_visits = Visit.objects.filter(
        animal_engagement=engagement, completed=False, visit_date__lt=timezone.now()
    ).order_by("-visit_date")

    # Obtener visitas completadas
    completed_visits = Visit.objects.filter(animal_engagement=engagement, completed=True).order_by(
        "-visit_date"
    )

    context = {
        "engagement": engagement,
        "animal": engagement.animal,
        "scheduled_visits": scheduled_visits,
        "overdue_visits": overdue_visits,
        "completed_visits": completed_visits,
    }

    return render(request, "engagements/animal_visits.html", context)
