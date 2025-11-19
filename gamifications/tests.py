import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from animals.models import Animal, History
from breeds.models import Breed
from engagements.models import AnimalEngagement
from shelters.models import Shelter

from .models import CareAction, CareIndicator, ShelterWalletBalance, VirtualWallet, WalletRecharge

User = get_user_model()


class GamificationDashboardViewTestCase(TestCase):
    """Tests for gamification dashboard view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(
            name="Test Shelter",
            email="shelter@test.com",
            food_unit_cost=2000,
            hygiene_unit_cost=2000,
        )
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="S",
        )

        # Create approved sponsorship
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        url = reverse("gamifications:dashboard", args=[self.animal.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_dashboard_view(self):
        """Test dashboard view displays correctly"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:dashboard", args=[self.animal.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gamifications/dashboard.html")

        # Check context
        self.assertEqual(response.context["animal"], self.animal)
        self.assertEqual(response.context["engagement"], self.engagement)
        self.assertIn("care_indicator", response.context)
        self.assertIn("wallet", response.context)
        self.assertIn("shelter_balance", response.context)

    def test_dashboard_creates_care_indicator(self):
        """Test that dashboard creates care indicator if not exists"""
        # Create a second animal with pending sponsorship (no CareIndicator created by signal)
        animal2 = Animal.objects.create(
            name="Buddy",
            birth_date=date(2021, 6, 15),
            sex="M",
            size="M",
            color="Black",
            breed=self.breed,
            shelter=self.shelter,
            availability="S",
        )
        engagement2 = AnimalEngagement.objects.create(
            user=self.user, animal=animal2, engagements_type="S", status="P"
        )

        self.client.login(username="testuser", password="pass123")

        # Ensure care indicator doesn't exist for pending engagement
        self.assertFalse(CareIndicator.objects.filter(engagement=engagement2).exists())

        # Approve the engagement manually to trigger signal
        engagement2.status = "A"
        engagement2.save()

        # Care indicator should now be created by signal
        self.assertTrue(CareIndicator.objects.filter(engagement=engagement2).exists())
        care_indicator = CareIndicator.objects.get(engagement=engagement2)
        self.assertEqual(care_indicator.food_level, 100)
        self.assertEqual(care_indicator.hygiene_level, 100)
        self.assertEqual(care_indicator.health_level, 100)

    def test_dashboard_other_user(self):
        """Test that user can only view their own sponsored animals"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="pass123"
        )

        self.client.login(username="otheruser", password="pass123")
        url = reverse("gamifications:dashboard", args=[self.animal.id])
        response = self.client.get(url)

        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_dashboard_adoption_not_sponsorship(self):
        """Test that dashboard only works for sponsorships"""
        # Change engagement to adoption
        self.engagement.engagements_type = "A"
        self.engagement.save()

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:dashboard", args=[self.animal.id])
        response = self.client.get(url)

        # Should return 404 (only sponsorships)
        self.assertEqual(response.status_code, 404)


class FeedAnimalViewTestCase(TestCase):
    """Tests for feed animal action"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(
            name="Test Shelter",
            email="shelter@test.com",
            food_unit_cost=2000,
            hygiene_unit_cost=2000,
        )
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="S",
        )

        # Create approved sponsorship (signal auto-creates CareIndicator)
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )

        # Get auto-created care indicator and modify values
        self.engagement.refresh_from_db()
        self.care_indicator = self.engagement.care_indicator
        self.care_indicator.food_level = 50
        self.care_indicator.save()

        # Create shelter balance with coins
        self.shelter_balance = ShelterWalletBalance.objects.create(
            user=self.user, shelter=self.shelter, balance=1000
        )

    def test_feed_animal_requires_login(self):
        """Test that feeding requires authentication"""
        url = reverse("gamifications:feed", args=[self.animal.id])
        response = self.client.post(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    @patch("gamifications.views.track_mission_progress")
    def test_feed_animal_success(self, mock_track_mission):
        """Test successful feeding action"""
        mock_track_mission.return_value = []  # No missions completed

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:feed", args=[self.animal.id])

        initial_food_level = self.care_indicator.food_level
        initial_balance = self.shelter_balance.balance
        food_cost = int(self.shelter.food_unit_cost / 10)

        response = self.client.post(url)

        # Should return success
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Care indicator should be updated
        self.care_indicator.refresh_from_db()
        self.assertEqual(self.care_indicator.food_level, min(100, initial_food_level + 10))

        # Balance should be reduced
        self.shelter_balance.refresh_from_db()
        self.assertEqual(self.shelter_balance.balance, initial_balance - food_cost)

        # Care action should be created
        self.assertTrue(
            CareAction.objects.filter(care_indicator=self.care_indicator, action_type="F").exists()
        )

    def test_feed_animal_insufficient_coins(self):
        """Test feeding with insufficient coins"""
        # Set balance to 0
        self.shelter_balance.balance = 0
        self.shelter_balance.save()

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:feed", args=[self.animal.id])
        response = self.client.post(url)

        # Should return error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("No tienes suficientes monedas", data["error"])

    def test_feed_animal_already_full(self):
        """Test feeding when food level is already at max"""
        # Set food level to 100
        self.care_indicator.food_level = 100
        self.care_indicator.save()

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:feed", args=[self.animal.id])
        response = self.client.post(url)

        # Should return error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("ya está al máximo", data["error"])

    def test_feed_animal_requires_post(self):
        """Test that feeding requires POST method"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:feed", args=[self.animal.id])
        response = self.client.get(url)

        # Should return method not allowed
        self.assertEqual(response.status_code, 405)


class CleanAnimalViewTestCase(TestCase):
    """Tests for clean animal action"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(
            name="Test Shelter",
            email="shelter@test.com",
            food_unit_cost=2000,
            hygiene_unit_cost=2000,
        )
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="S",
        )

        # Create approved sponsorship (signal auto-creates CareIndicator)
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )
        self.engagement.refresh_from_db()

        # Use signal-created care indicator and modify as needed
        self.care_indicator = self.engagement.care_indicator
        self.care_indicator.hygiene_level = 50
        self.care_indicator.save()

        # Create shelter balance with coins
        self.shelter_balance = ShelterWalletBalance.objects.create(
            user=self.user, shelter=self.shelter, balance=1000
        )

    @patch("gamifications.views.track_mission_progress")
    def test_clean_animal_success(self, mock_track_mission):
        """Test successful cleaning action"""
        mock_track_mission.return_value = []

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:clean", args=[self.animal.id])

        initial_hygiene_level = self.care_indicator.hygiene_level
        initial_balance = self.shelter_balance.balance
        hygiene_cost = int(self.shelter.hygiene_unit_cost / 10)

        response = self.client.post(url)

        # Should return success
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Care indicator should be updated
        self.care_indicator.refresh_from_db()
        self.assertEqual(self.care_indicator.hygiene_level, min(100, initial_hygiene_level + 10))

        # Balance should be reduced
        self.shelter_balance.refresh_from_db()
        self.assertEqual(self.shelter_balance.balance, initial_balance - hygiene_cost)

        # Care action should be created
        self.assertTrue(
            CareAction.objects.filter(care_indicator=self.care_indicator, action_type="H").exists()
        )

    def test_clean_animal_insufficient_coins(self):
        """Test cleaning with insufficient coins"""
        self.shelter_balance.balance = 0
        self.shelter_balance.save()

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:clean", args=[self.animal.id])
        response = self.client.post(url)

        # Should return error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])


class ContributeHealthViewTestCase(TestCase):
    """Tests for contribute to health event"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(
            name="Test Shelter",
            email="shelter@test.com",
            food_unit_cost=2000,
            hygiene_unit_cost=2000,
        )
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="S",
        )

        # Create approved sponsorship (signal auto-creates CareIndicator)
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )
        self.engagement.refresh_from_db()

        # Use signal-created care indicator (all at 100 by default)
        self.care_indicator = self.engagement.care_indicator

        # Create health event
        self.health_event = History.objects.create(
            animal=self.animal,
            history_type="T",
            description="Tratamiento médico",
            status="P",
            cost_coins=500,
            contributed_coins=0,
        )

        # Create shelter balance with coins
        self.shelter_balance = ShelterWalletBalance.objects.create(
            user=self.user, shelter=self.shelter, balance=1000
        )

    @patch("gamifications.views.track_mission_progress")
    def test_contribute_health_success(self, mock_track_mission):
        """Test successful health contribution"""
        mock_track_mission.return_value = []

        self.client.login(username="testuser", password="pass123")
        url = reverse(
            "gamifications:contribute_health",
            args=[self.animal.id, self.health_event.id],
        )

        contribution_amount = 100
        initial_balance = self.shelter_balance.balance

        response = self.client.post(
            url,
            data=json.dumps({"amount": contribution_amount}),
            content_type="application/json",
        )

        # Should return success
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["contribution"], contribution_amount)

        # Health event should be updated
        self.health_event.refresh_from_db()
        self.assertEqual(self.health_event.contributed_coins, contribution_amount)

        # Balance should be reduced
        self.shelter_balance.refresh_from_db()
        self.assertEqual(self.shelter_balance.balance, initial_balance - contribution_amount)

        # Care action should be created
        self.assertTrue(
            CareAction.objects.filter(care_indicator=self.care_indicator, action_type="M").exists()
        )

    def test_contribute_health_insufficient_coins(self):
        """Test contribution with insufficient coins"""
        self.shelter_balance.balance = 50
        self.shelter_balance.save()

        self.client.login(username="testuser", password="pass123")
        url = reverse(
            "gamifications:contribute_health",
            args=[self.animal.id, self.health_event.id],
        )

        response = self.client.post(
            url, data=json.dumps({"amount": 100}), content_type="application/json"
        )

        # Should return error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])

    def test_contribute_health_invalid_amount(self):
        """Test contribution with invalid amount"""
        self.client.login(username="testuser", password="pass123")
        url = reverse(
            "gamifications:contribute_health",
            args=[self.animal.id, self.health_event.id],
        )

        response = self.client.post(
            url, data=json.dumps({"amount": 0}), content_type="application/json"
        )

        # Should return error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])


class GetCareStatusViewTestCase(TestCase):
    """Tests for get care status API"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(
            name="Test Shelter",
            email="shelter@test.com",
            food_unit_cost=2000,
            hygiene_unit_cost=2000,
        )
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="S",
        )

        # Create approved sponsorship (signal auto-creates CareIndicator)
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )
        self.engagement.refresh_from_db()

        # Use signal-created care indicator and modify as needed
        self.care_indicator = self.engagement.care_indicator
        self.care_indicator.food_level = 80
        self.care_indicator.hygiene_level = 90
        self.care_indicator.health_level = 70
        self.care_indicator.save()

        # Create shelter balance
        ShelterWalletBalance.objects.create(user=self.user, shelter=self.shelter, balance=500)

    def test_get_care_status(self):
        """Test getting care status"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:get_status", args=[self.animal.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data["food_level"], 80)
        self.assertEqual(data["hygiene_level"], 90)
        self.assertEqual(data["health_level"], 70)
        self.assertEqual(data["wallet_balance"], 500)
        self.assertIn("overall_status", data)
        self.assertIn("needs_attention", data)


class RechargeWalletViewTestCase(TestCase):
    """Tests for recharge wallet view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")

    def test_recharge_wallet_requires_login(self):
        """Test that recharge page requires authentication"""
        url = reverse("gamifications:recharge_wallet")
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_recharge_wallet_view(self):
        """Test recharge wallet page displays correctly"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:recharge_wallet")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gamifications/recharge_wallet.html")

        # Check context
        self.assertIn("wallet", response.context)
        self.assertIn("packages", response.context)
        self.assertIn("shelters", response.context)


class CreateRechargeViewTestCase(TestCase):
    """Tests for create recharge view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        VirtualWallet.objects.create(user=self.user, balance=100)

    def test_create_recharge_requires_login(self):
        """Test that creating recharge requires authentication"""
        url = reverse("gamifications:create_recharge")
        response = self.client.post(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_create_recharge_success(self):
        """Test successful recharge creation"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:create_recharge")

        data = {
            "amount_cop": 10000,
            "shelter_id": self.shelter.id,
            "payment_method": "WOMPI",
        }

        response = self.client.post(url, data)

        # Should return success
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("reference", response_data)
        self.assertIn("integrity_signature", response_data)

        # Recharge should be created
        self.assertTrue(WalletRecharge.objects.filter(wallet__user=self.user).exists())

    def test_create_recharge_minimum_amount(self):
        """Test recharge with amount below minimum"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:create_recharge")

        data = {
            "amount_cop": 4000,  # Below minimum of 5000
            "shelter_id": self.shelter.id,
            "payment_method": "WOMPI",
        }

        response = self.client.post(url, data)

        # Should return error
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])

    def test_create_recharge_bonus_calculation(self):
        """Test that bonus coins are calculated correctly"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:create_recharge")

        # Test different amounts and their bonuses
        test_cases = [
            (10000, 0),  # No bonus for 10,000
            (20000, 200),  # 10% bonus for 20,000
            (50000, 750),  # 15% bonus for 50,000
            (100000, 2000),  # 20% bonus for 100,000
        ]

        for amount, expected_bonus in test_cases:
            data = {
                "amount_cop": amount,
                "shelter_id": self.shelter.id,
                "payment_method": "WOMPI",
            }

            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)

            response_data = json.loads(response.content)
            self.assertEqual(response_data["bonus"], expected_bonus)


class RechargeHistoryViewTestCase(TestCase):
    """Tests for recharge history view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.wallet = VirtualWallet.objects.create(user=self.user, balance=100)
        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")

    def test_recharge_history_requires_login(self):
        """Test that recharge history requires authentication"""
        url = reverse("gamifications:recharge_history")
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_recharge_history_view(self):
        """Test recharge history page"""
        # Create some recharges
        WalletRecharge.objects.create(
            wallet=self.wallet,
            amount_cop=10000,
            coins_received=1000,
            payment_method="WOMPI",
            status="A",
            shelter=self.shelter,
        )

        self.client.login(username="testuser", password="pass123")
        url = reverse("gamifications:recharge_history")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gamifications/recharge_history.html")
        self.assertIn("recharges", response.context)
        self.assertEqual(len(response.context["recharges"]), 1)
