import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "appfundationwDj.settings")
django.setup()

from users.models import CustomUser

USERNAME = "adminsolidaridad"
EMAIL = "admin@solidaridad-cucuta.com"
PASSWORD = "TuPasswordAqui123!"  # ¡CÁMBIALO!
FIRST_NAME = "Admin"
LAST_NAME = "Sistema"

print(f"🔵 Buscando usuario: {USERNAME}")

# Eliminar si existe
if CustomUser.objects.filter(username=USERNAME).exists():
    user = CustomUser.objects.get(username=USERNAME)
    user.delete()
    print(f"🗑️ Usuario anterior eliminado")

# Crear nuevo
user = CustomUser.objects.create_superuser(
    username=USERNAME, email=EMAIL, password=PASSWORD, first_name=FIRST_NAME, last_name=LAST_NAME
)

print(f"✅ Superusuario creado exitosamente")
print(f"   Username: {user.username}")
print(f"   Email: {user.email}")
print(f"   Is superuser: {user.is_superuser}")
print(f"   Is staff: {user.is_staff}")
print(f"   Is active: {user.is_active}")
