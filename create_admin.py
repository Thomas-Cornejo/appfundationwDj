import os
import django

print("🔵 Iniciando creación de superusuario...")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appfundationwDj.settings')
django.setup()

print("🔵 Django configurado correctamente")

from users.models import CustomUser

print("🔵 Modelo CustomUser importado")

# CAMBIA ESTOS VALORES
USERNAME = 'adminsolidaridad'
EMAIL = 'admin@solidaridad-cucuta.com'
PASSWORD = 'Admin2024Solidaridad!'  # ¡CÁMBIALO!
FIRST_NAME = 'Admin'
LAST_NAME = 'Sistema'

print(f"🔵 Verificando si existe usuario: {USERNAME}")

if not CustomUser.objects.filter(username=USERNAME).exists():
    print(f"🔵 Usuario no existe, creando...")
    CustomUser.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD,
        first_name=FIRST_NAME,
        last_name=LAST_NAME
    )
    print(f"✅ Superusuario creado: {USERNAME} ({EMAIL})")
else:
    print(f"⚠️ El usuario {USERNAME} ya existe")

print("🔵 Script finalizado")