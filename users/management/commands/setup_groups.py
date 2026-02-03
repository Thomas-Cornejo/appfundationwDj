from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea los grupos de usuarios con sus permisos correspondientes basados en los modelos reales"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("Configurando grupos y permisos del sistema"))
        self.stdout.write(self.style.WARNING("=" * 60 + "\n"))

        # ==================== SUPER ADMIN ====================
        self.stdout.write(self.style.HTTP_INFO("📋 Configurando Super Admin..."))
        super_admin, created = Group.objects.get_or_create(name="Super Admin")
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Grupo "Super Admin" creado'))
        else:
            self.stdout.write(self.style.WARNING('  → Grupo "Super Admin" ya existe'))

        # Super Admin tiene TODOS los permisos
        all_permissions = Permission.objects.all()
        super_admin.permissions.set(all_permissions)
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ {all_permissions.count()} permisos asignados (ACCESO TOTAL)\n")
        )

        # ==================== SHELTER ADMIN ====================
        self.stdout.write(self.style.HTTP_INFO("📋 Configurando Shelter Admin..."))
        shelter_admin, created = Group.objects.get_or_create(name="Shelter Admin")
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Grupo "Shelter Admin" creado'))
        else:
            self.stdout.write(self.style.WARNING('  → Grupo "Shelter Admin" ya existe'))

        shelter_admin_permissions = []

        # ANIMALES - Puede gestionar animales de su albergue
        try:
            animal_ct = ContentType.objects.get(app_label="animals", model="animal")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(codename="add_animal", content_type=animal_ct),
                    Permission.objects.get(codename="change_animal", content_type=animal_ct),
                    Permission.objects.get(codename="view_animal", content_type=animal_ct),
                    # NO puede eliminar animales
                ]
            )
            self.stdout.write("  ✓ Permisos de Animales configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Modelo Animal no encontrado"))

        # HISTORIAS MÉDICAS - Puede gestionar historias de animales de su albergue
        try:
            history_ct = ContentType.objects.get(app_label="animals", model="history")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(codename="add_history", content_type=history_ct),
                    Permission.objects.get(codename="change_history", content_type=history_ct),
                    Permission.objects.get(codename="view_history", content_type=history_ct),
                    Permission.objects.get(codename="delete_history", content_type=history_ct),
                ]
            )
            self.stdout.write("  ✓ Permisos de Historias Médicas configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Modelo History no encontrado"))

        # ENGAGEMENTS - Puede ver y aprobar/rechazar solicitudes de su albergue
        try:
            engagement_ct = ContentType.objects.get(
                app_label="engagements", model="animalengagement"
            )
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(
                        codename="change_animalengagement", content_type=engagement_ct
                    ),
                    Permission.objects.get(
                        codename="view_animalengagement", content_type=engagement_ct
                    ),
                    # NO puede crear ni eliminar engagements (lo hacen los usuarios)
                ]
            )
            self.stdout.write("  ✓ Permisos de Solicitudes configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Modelo AnimalEngagement no encontrado"))

        # VISITAS - Puede programar y gestionar visitas
        try:
            visit_ct = ContentType.objects.get(app_label="engagements", model="visit")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(codename="add_visit", content_type=visit_ct),
                    Permission.objects.get(codename="change_visit", content_type=visit_ct),
                    Permission.objects.get(codename="view_visit", content_type=visit_ct),
                    Permission.objects.get(codename="delete_visit", content_type=visit_ct),
                ]
            )
            self.stdout.write("  ✓ Permisos de Visitas configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Modelo Visit no encontrado"))

        # CARE INDICATORS - Puede ver indicadores de cuidado
        try:
            care_ct = ContentType.objects.get(app_label="gamifications", model="careindicator")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(codename="view_careindicator", content_type=care_ct),
                    Permission.objects.get(codename="change_careindicator", content_type=care_ct),
                ]
            )
            self.stdout.write("  ✓ Permisos de Indicadores de Cuidado configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo CareIndicator no encontrado"))

        # CARE ACTIONS - Puede ver acciones de cuidado
        try:
            action_ct = ContentType.objects.get(app_label="gamifications", model="careaction")
            shelter_admin_permissions.append(
                Permission.objects.get(codename="view_careaction", content_type=action_ct)
            )
            self.stdout.write("  ✓ Permisos de Acciones de Cuidado configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo CareAction no encontrado"))

        # WALLETS - Puede ver billeteras y transacciones de su albergue
        try:
            wallet_ct = ContentType.objects.get(app_label="gamifications", model="wallet")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(codename="view_wallet", content_type=wallet_ct),
                ]
            )
            self.stdout.write("  ✓ Permisos de Billeteras configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo Wallet no encontrado"))

        # WALLET TRANSACTIONS
        try:
            transaction_ct = ContentType.objects.get(
                app_label="gamifications", model="wallettransaction"
            )
            shelter_admin_permissions.append(
                Permission.objects.get(
                    codename="view_wallettransaction", content_type=transaction_ct
                )
            )
            self.stdout.write("  ✓ Permisos de Transacciones configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo WalletTransaction no encontrado"))

        # WALLET RECHARGES - Puede ver y aprobar recargas
        try:
            recharge_ct = ContentType.objects.get(app_label="gamifications", model="walletrecharge")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(
                        codename="view_walletrecharge", content_type=recharge_ct
                    ),
                    Permission.objects.get(
                        codename="change_walletrecharge", content_type=recharge_ct
                    ),
                ]
            )
            self.stdout.write("  ✓ Permisos de Recargas configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo WalletRecharge no encontrado"))

        # DIRECT PAYMENTS - Puede ver pagos directos
        try:
            payment_ct = ContentType.objects.get(app_label="gamifications", model="directpayment")
            shelter_admin_permissions.extend(
                [
                    Permission.objects.get(codename="view_directpayment", content_type=payment_ct),
                    Permission.objects.get(
                        codename="change_directpayment", content_type=payment_ct
                    ),
                ]
            )
            self.stdout.write("  ✓ Permisos de Pagos Directos configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo DirectPayment no encontrado"))

        # SHELTER - Solo puede VER su albergue (no editarlo)
        try:
            shelter_ct = ContentType.objects.get(app_label="shelters", model="shelter")
            shelter_admin_permissions.append(
                Permission.objects.get(codename="view_shelter", content_type=shelter_ct)
            )
            self.stdout.write("  ✓ Permisos de Albergue configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Modelo Shelter no encontrado"))

        # BREEDS - Solo puede ver razas
        try:
            breed_ct = ContentType.objects.get(app_label="breeds", model="breed")
            shelter_admin_permissions.append(
                Permission.objects.get(codename="view_breed", content_type=breed_ct)
            )
            self.stdout.write("  ✓ Permisos de Razas configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ✗ Modelo Breed no encontrado"))

        # MISSIONS - Solo puede ver misiones
        try:
            mission_ct = ContentType.objects.get(app_label="gamifications", model="mission")
            shelter_admin_permissions.append(
                Permission.objects.get(codename="view_mission", content_type=mission_ct)
            )
            self.stdout.write("  ✓ Permisos de Misiones configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo Mission no encontrado"))

        # RANKS - Solo puede ver rangos
        try:
            rank_ct = ContentType.objects.get(app_label="gamifications", model="rank")
            shelter_admin_permissions.append(
                Permission.objects.get(codename="view_rank", content_type=rank_ct)
            )
            self.stdout.write("  ✓ Permisos de Rangos configurados")
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Modelo Rank no encontrado"))

        shelter_admin.permissions.set(shelter_admin_permissions)
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ {len(shelter_admin_permissions)} permisos asignados\n")
        )

        # ==================== REGULAR USER ====================
        self.stdout.write(self.style.HTTP_INFO("📋 Configurando Regular User..."))
        regular_user, created = Group.objects.get_or_create(name="Regular User")
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Grupo "Regular User" creado'))
        else:
            self.stdout.write(self.style.WARNING('  → Grupo "Regular User" ya existe'))

        regular_user_permissions = []

        # ANIMALES - Solo puede ver
        try:
            animal_ct = ContentType.objects.get(app_label="animals", model="animal")
            regular_user_permissions.append(
                Permission.objects.get(codename="view_animal", content_type=animal_ct)
            )
            self.stdout.write("  ✓ Puede ver animales")
        except ContentType.DoesNotExist:
            pass

        # SHELTERS - Solo puede ver
        try:
            shelter_ct = ContentType.objects.get(app_label="shelters", model="shelter")
            regular_user_permissions.append(
                Permission.objects.get(codename="view_shelter", content_type=shelter_ct)
            )
            self.stdout.write("  ✓ Puede ver albergues")
        except ContentType.DoesNotExist:
            pass

        # BREEDS - Solo puede ver
        try:
            breed_ct = ContentType.objects.get(app_label="breeds", model="breed")
            regular_user_permissions.append(
                Permission.objects.get(codename="view_breed", content_type=breed_ct)
            )
            self.stdout.write("  ✓ Puede ver razas")
        except ContentType.DoesNotExist:
            pass

        # ENGAGEMENTS - Solo puede ver sus propios (gestionado en vistas)
        try:
            engagement_ct = ContentType.objects.get(
                app_label="engagements", model="animalengagement"
            )
            regular_user_permissions.append(
                Permission.objects.get(codename="view_animalengagement", content_type=engagement_ct)
            )
            self.stdout.write("  ✓ Puede ver sus solicitudes")
        except ContentType.DoesNotExist:
            pass

        # CARE INDICATORS - Puede ver y gestionar sus propios
        try:
            care_ct = ContentType.objects.get(app_label="gamifications", model="careindicator")
            regular_user_permissions.extend(
                [
                    Permission.objects.get(codename="view_careindicator", content_type=care_ct),
                    Permission.objects.get(codename="change_careindicator", content_type=care_ct),
                ]
            )
            self.stdout.write("  ✓ Puede gestionar indicadores de cuidado")
        except ContentType.DoesNotExist:
            pass

        # CARE ACTIONS - Puede crear y ver sus propias acciones
        try:
            action_ct = ContentType.objects.get(app_label="gamifications", model="careaction")
            regular_user_permissions.extend(
                [
                    Permission.objects.get(codename="add_careaction", content_type=action_ct),
                    Permission.objects.get(codename="view_careaction", content_type=action_ct),
                ]
            )
            self.stdout.write("  ✓ Puede realizar acciones de cuidado")
        except ContentType.DoesNotExist:
            pass

        # WALLETS - Puede ver y gestionar su billetera
        try:
            wallet_ct = ContentType.objects.get(app_label="gamifications", model="wallet")
            regular_user_permissions.extend(
                [
                    Permission.objects.get(codename="view_wallet", content_type=wallet_ct),
                ]
            )
            self.stdout.write("  ✓ Puede ver su billetera")
        except ContentType.DoesNotExist:
            pass

        # WALLET TRANSACTIONS - Puede ver sus transacciones
        try:
            transaction_ct = ContentType.objects.get(
                app_label="gamifications", model="wallettransaction"
            )
            regular_user_permissions.append(
                Permission.objects.get(
                    codename="view_wallettransaction", content_type=transaction_ct
                )
            )
            self.stdout.write("  ✓ Puede ver sus transacciones")
        except ContentType.DoesNotExist:
            pass

        # WALLET RECHARGES - Puede crear recargas
        try:
            recharge_ct = ContentType.objects.get(app_label="gamifications", model="walletrecharge")
            regular_user_permissions.extend(
                [
                    Permission.objects.get(codename="add_walletrecharge", content_type=recharge_ct),
                    Permission.objects.get(
                        codename="view_walletrecharge", content_type=recharge_ct
                    ),
                ]
            )
            self.stdout.write("  ✓ Puede recargar billetera")
        except ContentType.DoesNotExist:
            pass

        # DIRECT PAYMENTS - Puede crear pagos directos
        try:
            payment_ct = ContentType.objects.get(app_label="gamifications", model="directpayment")
            regular_user_permissions.extend(
                [
                    Permission.objects.get(codename="add_directpayment", content_type=payment_ct),
                    Permission.objects.get(codename="view_directpayment", content_type=payment_ct),
                ]
            )
            self.stdout.write("  ✓ Puede hacer pagos directos")
        except ContentType.DoesNotExist:
            pass

        # MISSIONS - Puede ver misiones
        try:
            mission_ct = ContentType.objects.get(app_label="gamifications", model="mission")
            regular_user_permissions.append(
                Permission.objects.get(codename="view_mission", content_type=mission_ct)
            )
            self.stdout.write("  ✓ Puede ver misiones")
        except ContentType.DoesNotExist:
            pass

        # USER MISSION PROGRESS - Puede gestionar su progreso
        try:
            progress_ct = ContentType.objects.get(
                app_label="gamifications", model="usermissionprogress"
            )
            regular_user_permissions.extend(
                [
                    Permission.objects.get(
                        codename="view_usermissionprogress", content_type=progress_ct
                    ),
                    Permission.objects.get(
                        codename="add_usermissionprogress", content_type=progress_ct
                    ),
                    Permission.objects.get(
                        codename="change_usermissionprogress", content_type=progress_ct
                    ),
                ]
            )
            self.stdout.write("  ✓ Puede gestionar progreso de misiones")
        except ContentType.DoesNotExist:
            pass

        # RANKS - Solo puede ver rangos
        try:
            rank_ct = ContentType.objects.get(app_label="gamifications", model="rank")
            regular_user_permissions.append(
                Permission.objects.get(codename="view_rank", content_type=rank_ct)
            )
            self.stdout.write("  ✓ Puede ver rangos")
        except ContentType.DoesNotExist:
            pass

        regular_user.permissions.set(regular_user_permissions)
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ {len(regular_user_permissions)} permisos asignados\n")
        )
