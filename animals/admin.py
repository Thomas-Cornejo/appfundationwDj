from django.contrib import admin
from django.utils.html import format_html
from .models import Animal, History
from shelters.models import Shelter

class HistoryInline(admin.StackedInline):
    """Inline to manage the animal's medical history."""
    model = History
    extra = 1
    fieldsets = (
        (None, {
            "fields": ("history_type", "description", "location_found", "entry_date")
        }),
    )
    readonly_fields = ("entry_date",)
    show_change_link = True
    
    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete history"""
        if request.user.is_superadmin():
            return True
        return False


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = [
        "name", 
        "breed", 
        "age",
        "sex", 
        "size", 
        "color", 
        "shelter", 
        "availability",
        "is_active",
        "preview_image"
    ]
    
    list_filter = [
        "shelter",
        "breed__species", 
        "availability",
        "sex", 
        "size",
        "is_active"
    ]
    
    search_fields = [
        "name", 
        "shelter__name", 
        "breed__name"
    ]
    
    readonly_fields = ["created_at", "updated_at", "age"]
    
    inlines = [HistoryInline]

    fieldsets = (
        ("Información Básica", {
            "fields": (
                "name",
                "birth_date",
                "age",
                "breed",
                "sex",
                "size",
                "color",
            )
        }),
        ("Albergue y Disponibilidad", { 
            "fields": (
                "shelter",
                "availability",
                "is_active",
            )
        }),
        ("Imagen", {
            "fields": ("imagen",)
        }),
        ("Metadatos", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def preview_image(self, obj):
        """Shows a preview of the animal's image"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="120" height="120" style="border-radius:10px; object-fit: cover;" />',
                obj.imagen.url,
            )
        return format_html(
            '<div style="width:120px; height:120px; background:#e0e0e0; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#666;">Sin imagen</div>'
        )
    preview_image.short_description = "Vista previa"
    
    
    def get_queryset(self, request):
        """
        Filter animals by user role:
        - Super Admin: Sees ALL animals
        - Shelter Admin: Only sees animals in THEIR shelter
        - Regular User: Does not have admin access
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_superadmin():
            return qs
        
        if request.user.is_shelter_admin() and request.user.shelter:
            return qs.filter(shelter=request.user.shelter)
        
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Restrict ForeignKey options based on permissions:
        - Super Admin: Sees all hostels
        - Shelter Admin: Only sees THEIR hostel (and is pre-selected)
        """
        if db_field.name == "shelter":
            if request.user.is_superuser or request.user.is_superadmin():
                pass
            
            elif request.user.is_shelter_admin() and request.user.shelter:
                kwargs["queryset"] = Shelter.objects.filter(id=request.user.shelter.id)
                if not kwargs.get('initial'):
                    kwargs["initial"] = request.user.shelter.id
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_delete_permission(self, request, obj=None):
        """
        Only Super Admin can delete animals. 
        Shelter Admin cannot delete animals (to prevent data loss).
        """
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        return False
    
    def has_add_permission(self, request):
        """
        Super Admins and Shelter Admins can add animals.
        Regular Users cannot.
        """
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        if request.user.is_shelter_admin():
            return True
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Super Admin and Shelter Admin can edit animals.
        Shelter Admin can only edit animals in their shelter.
        """
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        
        if request.user.is_shelter_admin():
            if obj is None:
                return True
            return obj.shelter == request.user.shelter
        
        return False
    
    actions = ['mark_as_available_for_adoption', 'mark_as_available_for_sponsorship', 'mark_as_available_for_both']
    
    def mark_as_available_for_adoption(self, request, queryset):
        """Mark as available for adoption only"""
        updated = queryset.update(availability='A')
        self.message_user(request, f"{updated} animal(es) marcado(s) como disponible para adopción.")
    mark_as_available_for_adoption.short_description = "Marcar como disponible para adopción"
    
    def mark_as_available_for_sponsorship(self, request, queryset):
        """Mark as available for sponsorship only"""
        updated = queryset.update(availability='S')
        self.message_user(request, f"{updated} animal(es) marcado(s) como disponible para apadrinamiento.")
    mark_as_available_for_sponsorship.short_description = "Marcar como disponible para apadrinamiento"
    
    def mark_as_available_for_both(self, request, queryset):
        """Mark as available for both"""
        updated = queryset.update(availability='B')
        self.message_user(request, f"{updated} animal(es) marcado(s) como disponible para ambos.")
    mark_as_available_for_both.short_description = "Marcar como disponible para ambos"


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    """Admin to manage medical history directly"""
    list_display = ["animal", "history_type", "entry_date", "description_preview"]
    list_filter = ["history_type", "animal__shelter", "entry_date"]
    search_fields = ["animal__name", "description"]
    readonly_fields = ["entry_date"]
    
    fieldsets = (
        ("Información del Evento", {
            "fields": ("animal", "history_type", "description", "location_found", "entry_date")
        }),
    )
    
    def description_preview(self, obj):
        """Shows a short preview of the description"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "-"
    description_preview.short_description = "Descripción"
    
    def get_queryset(self, request):
        """Filter history by animal shelter"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_superadmin():
            return qs
        
        if request.user.is_shelter_admin() and request.user.shelter:
            return qs.filter(animal__shelter=request.user.shelter)
        
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict visible animals when creating history"""
        if db_field.name == "animal":
            if not (request.user.is_superuser or request.user.is_superadmin()):
                if request.user.is_shelter_admin() and request.user.shelter:
                    kwargs["queryset"] = Animal.objects.filter(shelter=request.user.shelter)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete history"""
        return request.user.is_superuser or request.user.is_superadmin()