from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Animal, Breed
from datetime import date

def animal_list(request, *args, **kwargs):
    type = kwargs.get("type")

    breeds = Breed.objects.all()
    selected_breed = request.GET.get('breed')
    selected_birth_date = request.GET.get('birth_date')
    selected_size = request.GET.get('size')

    if type == "adoption":  
        animals = Animal.objects.filter(is_active=True, availability__in=["A", "B"])
        template_name = "animals/adoption.html"
    elif type == "sponsorship":
        animals = Animal.objects.filter(is_active=True, availability__in=["S", "B"])
        template_name = "animals/sponsorship.html"
    else:
        animals = Animal.objects.none()
        template_name = "animals/adoption.html"

    if selected_breed:
        animals = animals.filter(breed_id=selected_breed)

    if selected_size:
        animals = animals.filter(size=selected_size)

    if selected_birth_date:
        today = date.today()
        filtered_animals = []
        for a in animals:
            age = today.year - a.birth_date.year - (
                (today.month, today.day) < (a.birth_date.month, a.birth_date.day)
            )
            if selected_birth_date == "joven" and age <= 2:
                filtered_animals.append(a)
            elif selected_birth_date == "adulto" and 3 <= age <= 7:
                filtered_animals.append(a)
            elif selected_birth_date == "senior" and age >= 8:
                filtered_animals.append(a)
        animals = filtered_animals
    
    if not selected_birth_date:
        animals = list(animals)

    paginator = Paginator(animals, 8) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "breeds": breeds,
        "page_obj": page_obj,
        "selected_breed": selected_breed or "",
        "selected_birth_date": selected_birth_date or "",
        "selected_size": selected_size or "",
        "type": type,
    }

    return render(request, template_name, context)


def animal_detail(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)
    return render(request, "animals/animal_detail.html", {"animal": animal})