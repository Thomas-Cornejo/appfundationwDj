import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appfundationwDj.settings')
django.setup()

from users.models import CustomUser

USERNAME = 'adminsolidaridad'
NEW_PASSWORD = 'SolidaridadAdmin2024!'  # ← PON UNA NUEVA AQUÍ

user = CustomUser.objects.get(username=USERNAME)
user.set_password(NEW_PASSWORD)
user.save()

print(f"✅ Nueva contraseña establecida para: {user.username}")
print(f"   Username: {USERNAME}")
print(f"   Password: {NEW_PASSWORD}")