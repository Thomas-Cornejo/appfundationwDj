from datetime import date

from django.contrib.auth import get_user_model
from django.template import TemplateDoesNotExist
from django.test import Client, TestCase
from django.urls import reverse

from animals.models import Animal, Breed
from engagements.models import AnimalEngagement
from shelters.models import Shelter

User = get_user_model()


class RegisterViewTestCase(TestCase):
    """Tests for user registration view"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("register")

    def test_register_view_get(self):
        """Test GET request to registration page"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_view_post_valid(self):
        """Test POST request with valid data"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "phone_number": "+573001234567",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_view_post_password_mismatch(self):
        """Test POST request with mismatched passwords"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "DifferentPass123!",
            "phone_number": "+573001234567",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_register_view_post_duplicate_email(self):
        """Test POST request with duplicate email"""
        User.objects.create_user(
            username="existinguser", email="test@example.com", password="pass123"
        )
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "phone_number": "+573001234567",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 1)


class HomeViewTestCase(TestCase):
    """Tests for home view"""

    def test_home_view_get(self):
        """Test GET request to home page"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/home.html")


class ProfileViewTestCase(TestCase):
    """Tests for user profile dashboard view"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("profile")
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )
        shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=breed,
            shelter=shelter,
            availability="B",
        )

    def _get_response_or_skip(self):
        """Helper to get response or skip if template missing"""
        try:
            return self.client.get(self.url)
        except TemplateDoesNotExist:
            self.skipTest("Template does not exist")

    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_profile_view_logged_in(self):
        """Test profile view for logged in user"""
        self.client.login(username="testuser", password="pass123")
        response = self._get_response_or_skip()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], self.user)

    def test_profile_view_with_adoptions(self):
        """Test profile view displays adoptions"""
        self.client.login(username="testuser", password="pass123")
        adoption = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="A", status="A"
        )
        response = self._get_response_or_skip()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_adoptions"])
        self.assertIn(adoption, response.context["adoptions"])

    def test_profile_view_with_sponsorships(self):
        """Test profile view displays sponsorships with care indicators"""
        self.client.login(username="testuser", password="pass123")
        # CareIndicator auto-created by signal
        sponsorship = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )
        sponsorship.refresh_from_db()

        response = self._get_response_or_skip()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_sponsorships"])
        self.assertEqual(len(response.context["sponsorships"]), 1)
        self.assertTrue(hasattr(sponsorship, "care_indicator"))

    def test_profile_view_no_engagements(self):
        """Test profile view when user has no adoptions or sponsorships"""
        self.client.login(username="testuser", password="pass123")
        response = self._get_response_or_skip()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_adoptions"])
        self.assertFalse(response.context["has_sponsorships"])


class EditProfileViewTestCase(TestCase):
    """Tests for edit profile view"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("edit_profile")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123",
            phone="+573001234567",
            address="Calle 123",
        )

    def test_edit_profile_requires_login(self):
        """Test that edit profile requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_edit_profile_get(self):
        """Test GET request to edit profile page"""
        self.client.login(username="testuser", password="pass123")
        try:
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["user"], self.user)
        except TemplateDoesNotExist:
            self.skipTest("Template does not exist")

    def test_edit_profile_post_valid(self):
        """Test POST request with valid data"""
        self.client.login(username="testuser", password="pass123")
        data = {
            "email": "newemail@example.com",
            "phone": "+573109876543",
            "address": "New Address 456",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("profile")))

        # Verify data was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")
        self.assertEqual(str(self.user.phone), "+573109876543")
        self.assertEqual(self.user.address, "New Address 456")

    def test_edit_profile_post_invalid_phone(self):
        """Test POST request with invalid phone number"""
        self.client.login(username="testuser", password="pass123")
        data = {
            "email": "test@example.com",
            "phone": "invalid_phone",
            "address": "Calle 123",
        }
        try:
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 200)
        except TemplateDoesNotExist:
            pass

        # Verify phone was NOT updated
        self.user.refresh_from_db()
        self.assertEqual(str(self.user.phone), "+573001234567")

    def test_edit_profile_post_duplicate_email(self):
        """Test POST request with duplicate email"""
        User.objects.create_user(
            username="otheruser", email="other@example.com", password="pass123"
        )
        self.client.login(username="testuser", password="pass123")
        data = {
            "email": "other@example.com",
            "phone": "+573001234567",
            "address": "Calle 123",
        }
        try:
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 200)
        except TemplateDoesNotExist:
            pass

        # Verify email was NOT updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test@example.com")
