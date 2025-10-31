from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from animals.models import Animal
from .models import AnimalEngagement
from .forms import AdoptionForm
from .utils import generate_adoption_pdf
from datetime import datetime
import os

@login_required
def adopt_animal(request, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    user = request.user

    existing = AnimalEngagement.objects.filter(
        user=user, animal=animal, engagements_type='A', status__in=['P', 'A']
    ).first()

    if existing:
        return render(request, 'engagements/already_applied.html', {
            'engagement': existing,
            'animal': animal
        })

    if request.method == 'POST':
        form = AdoptionForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            
            engagement = AnimalEngagement.objects.create(
                user=user,
                animal=animal,
                engagements_type='A',
                status='P',
                form_data=form_data
            )
            
            pdf_buffer = generate_adoption_pdf(engagement, form_data)
            
            filename = f"Solicitud_Adopcion_{user.username}_para_{animal.name}.pdf"
            filename = filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            engagement.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)
            
            messages.success(request, f'¡Solicitud enviada para {animal.name}!')
            return redirect('adoption_success', engagement_id=engagement.id)
    else:
        form = AdoptionForm()

    return render(request, 'engagements/adoption_form.html', {'form': form, 'animal': animal})

@login_required
def adoption_success(request, engagement_id):
    engagement = get_object_or_404(AnimalEngagement, pk=engagement_id, user=request.user)
    return render(request, 'engagements/adoption_success.html', {'engagement': engagement})

@login_required
def download_pdf(request, engagement_id):
    """View to download the PDF with the correct name"""
    engagement = get_object_or_404(AnimalEngagement, pk=engagement_id)
    
    if not (request.user == engagement.user or request.user.is_staff):
        raise Http404("No tienes permiso para ver este archivo")
    
    if not engagement.pdf_file:
        raise Http404("No hay PDF disponible")
    
    filename = f"Solicitud_Adopcion_{engagement.user.username}_para_{engagement.animal.name}.pdf"
    filename = filename.replace(' ', '_')
    
    try:
        pdf_file = engagement.pdf_file.open('rb')
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        raise Http404("Error al abrir el archivo")