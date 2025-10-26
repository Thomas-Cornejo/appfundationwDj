from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Animal, Breed


def animal_list(request):
    breeds = Breed.objects.all()

    selected_breed = request.GET.get('breed')
    selected_birth_date = request.GET.get('birth_date')
    selected_size = request.GET.get('size')

    animals = Animal.objects.all()
    
    if selected_breed:
        animals = animals.filter(breed_id=selected_breed)

    if selected_birth_date:
        if selected_birth_date == "joven":
            animals = animals.filter(age__lte=2)
        elif selected_birth_date == "adulto":
            animals = animals.filter(age__gte=3, age__lte=7)
        elif selected_birth_date == "senior":
            animals = animals.filter(age__gte=8)

    if selected_size:
        animals = animals.filter(size=selected_size)

    paginator = Paginator(animals, 8) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "breeds": breeds,
        "page_obj": page_obj,
        "selected_breed": selected_breed or "",
        "selected_birth_date": selected_birth_date or "",
        "selected_size": selected_size or "",
    }

    return render(request, "animals/adoption.html", context)


def animal_detail(request, animal_id):
    """
    Vista de detalle de un animal específico.
    """
    animal = get_object_or_404(Animal, id=animal_id)

    context = {
        "animal": animal
    }

    return render(request, "animals/animal_detail.html", context)
