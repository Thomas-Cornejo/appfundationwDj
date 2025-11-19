from datetime import date, timedelta
from io import BytesIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from animals.models import Animal
from breeds.models import Breed
from shelters.models import Shelter

from .models import AnimalEngagement, Visit

User = get_user_model()


class AdoptAnimalViewTestCase(TestCase):
    """Tests for adopt animal view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="A",
        )

    def test_adopt_animal_requires_login(self):
        """Test that adoption requires authentication"""
        url = reverse("adopt_animal", args=[self.animal.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_adopt_animal_get(self):
        """Test GET request to adoption form"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("adopt_animal", args=[self.animal.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "engagements/adoption_form.html")
        self.assertEqual(response.context["animal"], self.animal)

    @patch("engagements.views.generate_adoption_pdf")
    def test_adopt_animal_post_valid(self, mock_pdf):
        """Test POST request with valid adoption form"""
        # Mock PDF generation
        mock_pdf.return_value = BytesIO(b"fake pdf content")

        self.client.login(username="testuser", password="pass123")
        url = reverse("adopt_animal", args=[self.animal.id])

        data = {
            "full_name": "Test User",
            "phone": "+573001234567",
            "address": "Calle 123",
            "city": "Bogotá",
            "occupation": "Engineer",
            "housing_type": "Casa",
            "has_outdoor_space": True,
            "has_experience": True,
            "has_other_pets": False,
            "other_pets_description": "",
            "reason_for_adoption": "I love dogs",
        }

        response = self.client.post(url, data)

        # Should redirect to success page
        self.assertEqual(response.status_code, 302)

        # Engagement should be created
        engagement = AnimalEngagement.objects.filter(
            user=self.user, animal=self.animal, engagements_type="A"
        ).first()
        self.assertIsNotNone(engagement)
        self.assertEqual(engagement.status, "P")  # Pending
        self.assertTrue(mock_pdf.called)

    def test_adopt_animal_already_applied(self):
        """Test adopting when user already has pending/approved application"""
        self.client.login(username="testuser", password="pass123")

        # Create existing pending application
        existing = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="A", status="P"
        )

        url = reverse("adopt_animal", args=[self.animal.id])
        response = self.client.get(url)

        # Should show already applied template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "engagements/already_applied.html")
        self.assertEqual(response.context["engagement"], existing)

    def test_adopt_animal_not_found(self):
        """Test adopting non-existent animal"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("adopt_animal", args=[99999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class SponsorAnimalViewTestCase(TestCase):
    """Tests for sponsor animal view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        # Create test data
        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
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

    def test_sponsor_animal_requires_login(self):
        """Test that sponsorship requires authentication"""
        url = reverse("sponsor_animal", args=[self.animal.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_sponsor_animal_get(self):
        """Test GET request to sponsorship form"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("sponsor_animal", args=[self.animal.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "engagements/sponsorship_form.html")
        self.assertEqual(response.context["animal"], self.animal)

    @patch("engagements.views.generate_sponsorship_pdf")
    def test_sponsor_animal_post_valid(self, mock_pdf):
        """Test POST request with valid sponsorship form"""
        # Mock PDF generation
        mock_pdf.return_value = BytesIO(b"fake pdf content")

        self.client.login(username="testuser", password="pass123")
        url = reverse("sponsor_animal", args=[self.animal.id])

        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+573001234567",
            "age_range": "26-35",
            "occupation": "Engineer",
            "has_pet_experience": "some",
            "reason_for_sponsorship": "I love animals",
            "availability_hours": "1-2",
            "motivation_level": "regular",
            "notification_preferences": "important",
            "accept_terms": True,
        }

        response = self.client.post(url, data)

        # Should redirect to success page
        self.assertEqual(response.status_code, 302)

        # Engagement should be created
        engagement = AnimalEngagement.objects.filter(
            user=self.user, animal=self.animal, engagements_type="S"
        ).first()
        self.assertIsNotNone(engagement)
        self.assertEqual(engagement.status, "P")  # Pending
        self.assertTrue(mock_pdf.called)

    def test_sponsor_animal_already_applied(self):
        """Test sponsoring when user already has pending/approved application"""
        self.client.login(username="testuser", password="pass123")

        # Create existing approved sponsorship
        existing = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )

        url = reverse("sponsor_animal", args=[self.animal.id])
        response = self.client.get(url)

        # Should show already applied template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "engagements/already_applied.html")
        self.assertEqual(response.context["engagement"], existing)


class EngagementSuccessViewTestCase(TestCase):
    """Tests for engagement success view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="A",
        )

        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="A", status="P"
        )

    def test_engagement_success_requires_login(self):
        """Test that success page requires authentication"""
        url = reverse("engagement_success", args=[self.engagement.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_engagement_success_view(self):
        """Test engagement success page"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("engagement_success", args=[self.engagement.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "engagements/engagement_success.html")
        self.assertEqual(response.context["engagement"], self.engagement)
        self.assertEqual(response.context["animal"], self.animal)

    def test_engagement_success_other_user(self):
        """Test that user can only view their own engagements"""
        # Create another user
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="pass123"
        )

        self.client.login(username="otheruser", password="pass123")
        url = reverse("engagement_success", args=[self.engagement.id])
        response = self.client.get(url)

        # Should return 404
        self.assertEqual(response.status_code, 404)


class DownloadPDFViewTestCase(TestCase):
    """Tests for download PDF view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="A",
        )

        # Create engagement with fake PDF
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="A", status="P"
        )
        fake_pdf = SimpleUploadedFile(
            "test.pdf", b"fake pdf content", content_type="application/pdf"
        )
        self.engagement.pdf_file = fake_pdf
        self.engagement.save()

    def test_download_pdf_requires_login(self):
        """Test that PDF download requires authentication"""
        url = reverse("download_pdf", args=[self.engagement.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_download_pdf_owner(self):
        """Test PDF download by engagement owner"""
        self.client.login(username="testuser", password="pass123")
        url = reverse("download_pdf", args=[self.engagement.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("Content-Disposition", response)

    def test_download_pdf_staff(self):
        """Test PDF download by staff user"""
        staff_user = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="pass123", is_staff=True
        )

        self.client.login(username="staffuser", password="pass123")
        url = reverse("download_pdf", args=[self.engagement.id])
        response = self.client.get(url)

        # Staff should be able to download
        self.assertEqual(response.status_code, 200)

    def test_download_pdf_other_user(self):
        """Test that other users cannot download PDF"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="pass123"
        )

        self.client.login(username="otheruser", password="pass123")
        url = reverse("download_pdf", args=[self.engagement.id])
        response = self.client.get(url)

        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_download_pdf_no_file(self):
        """Test download when engagement has no PDF"""
        # Create engagement without PDF
        engagement_no_pdf = AnimalEngagement.objects.create(
            user=self.user,
            animal=self.animal,
            engagements_type="S",
            status="P",
        )

        self.client.login(username="testuser", password="pass123")
        url = reverse("download_pdf", args=[engagement_no_pdf.id])
        response = self.client.get(url)

        # Should return 404
        self.assertEqual(response.status_code, 404)


class AnimalVisitsViewTestCase(TestCase):
    """Tests for animal visits view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        self.breed = Breed.objects.create(name="Labrador", species="C")
        self.animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
            availability="A",
        )

        # Create approved adoption
        self.engagement = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="A", status="A"
        )

    def test_animal_visits_requires_login(self):
        """Test that visits page requires authentication"""
        url = reverse("animal_visits", args=[self.engagement.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_animal_visits_view(self):
        """Test visits page with different visit statuses"""
        self.client.login(username="testuser", password="pass123")

        # Create different types of visits
        now = timezone.now()

        # Scheduled visit (future)
        scheduled_visit = Visit.objects.create(
            animal_engagement=self.engagement,
            visit_date=now + timedelta(days=7),
            completed=False,
        )

        # Overdue visit (past, not completed)
        overdue_visit = Visit.objects.create(
            animal_engagement=self.engagement,
            visit_date=now - timedelta(days=7),
            completed=False,
        )

        # Completed visit
        completed_visit = Visit.objects.create(
            animal_engagement=self.engagement,
            visit_date=now - timedelta(days=14),
            completed=True,
            evaluation=5,
            notes="Everything is great!",
        )

        url = reverse("animal_visits", args=[self.engagement.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "engagements/animal_visits.html")

        # Check context
        self.assertEqual(response.context["engagement"], self.engagement)
        self.assertIn(scheduled_visit, response.context["scheduled_visits"])
        self.assertIn(overdue_visit, response.context["overdue_visits"])
        self.assertIn(completed_visit, response.context["completed_visits"])

    def test_animal_visits_other_user(self):
        """Test that user can only view their own adoption visits"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="pass123"
        )

        self.client.login(username="otheruser", password="pass123")
        url = reverse("animal_visits", args=[self.engagement.id])
        response = self.client.get(url)

        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_animal_visits_sponsorship(self):
        """Test that visits view only works for adoptions"""
        # Create sponsorship
        sponsorship = AnimalEngagement.objects.create(
            user=self.user, animal=self.animal, engagements_type="S", status="A"
        )

        self.client.login(username="testuser", password="pass123")
        url = reverse("animal_visits", args=[sponsorship.id])
        response = self.client.get(url)

        # Should return 404 (only adoptions have visits)
        self.assertEqual(response.status_code, 404)

    def test_animal_visits_pending_engagement(self):
        """Test that visits view only works for approved engagements"""
        # Create pending adoption
        pending = AnimalEngagement.objects.create(
            user=self.user,
            animal=self.animal,
            engagements_type="A",
            status="P",  # Pending
        )

        self.client.login(username="testuser", password="pass123")
        url = reverse("animal_visits", args=[pending.id])
        response = self.client.get(url)

        # Should return 404 (only approved adoptions)
        self.assertEqual(response.status_code, 404)
