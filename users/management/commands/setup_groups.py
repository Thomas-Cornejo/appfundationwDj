from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from animals.models import Animal
from engagements.models import AnimalEngagement
from shelters.models import Shelter


class Command(BaseCommand):
    help = "Create user groups and assign permissions"

    def handle(self, *args, **kwargs):
        super_admin_group, _ = Group.objects.get_or_create(name="Super Admin")
        shelter_admin_group, _ = Group.objects.get_or_create(name="Shelter Admin")
        regular_user_group, _ = Group.objects.get_or_create(name="Regular User")

        super_admin_group.permissions.clear()
        shelter_admin_group.permissions.clear()
        regular_user_group.permissions.clear()

        all_permissions = Permission.objects.all()
        super_admin_group.permissions.set(all_permissions)
        self.stdout.write(self.style.SUCCESS("Super Admin: All permissions assigned"))

        shelter_admin_permissions = [
            "view_animal",
            "add_animal",
            "change_animal",
            "view_animalengagement",
            "change_animalengagement",
            "view_shelter",
        ]

        for perm_codename in shelter_admin_permissions:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                shelter_admin_group.permissions.add(permission)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Permission not found: {perm_codename}")
                )

        self.stdout.write(self.style.SUCCESS("Shelter Admin: Assigned Permissions"))

        regular_user_permissions = [
            "view_animal",
            "add_animalengagement",
            "view_animalengagement",
        ]

        for perm_codename in regular_user_permissions:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                regular_user_group.permissions.add(permission)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Permission not found: {perm_codename}")
                )

        self.stdout.write(self.style.SUCCESS("Regular User: Assigned Permissions"))

        self.stdout.write(
            self.style.SUCCESS("\nAll groups and permissions configured correctly")
        )
