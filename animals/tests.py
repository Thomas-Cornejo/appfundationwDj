from datetime import date, timedelta

from django.test import Client, TestCase
from django.urls import reverse

from breeds.models import Breed
from shelters.models import Shelter

from .models import Animal


class AnimalListViewTestCase(TestCase):
    """Tests for animal list view (adoption and sponsorship)"""

    def setUp(self):
        self.client = Client()

        # Create test data
        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        self.breed1 = Breed.objects.create(name="Labrador", species="C")
        self.breed2 = Breed.objects.create(name="Poodle", species="C")

        # Create animals with different attributes
        self.animal_adoption = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),  # ~5 years old (adulto)
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed1,
            shelter=self.shelter,
            availability="A",  # Only adoption
            is_active=True,
        )

        self.animal_sponsorship = Animal.objects.create(
            name="Luna",
            birth_date=date(2022, 1, 1),  # ~2 years old (joven)
            sex="H",
            size="M",
            color="White",
            breed=self.breed2,
            shelter=self.shelter,
            availability="S",  # Only sponsorship
            is_active=True,
        )

        self.animal_both = Animal.objects.create(
            name="Rocky",
            birth_date=date(2015, 1, 1),  # ~10 years old (senior)
            sex="M",
            size="P",
            color="Black",
            breed=self.breed1,
            shelter=self.shelter,
            availability="B",  # Both
            is_active=True,
        )

        # Inactive animal should not appear
        self.animal_inactive = Animal.objects.create(
            name="Inactive",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Gray",
            breed=self.breed1,
            shelter=self.shelter,
            availability="A",
            is_active=False,  # Inactive
        )

    def test_adoption_list_view(self):
        """Test adoption list view"""
        url = reverse("adoption_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "animals/adoption.html")

        # Should include animals available for adoption (A or B)
        animals_in_page = [animal for animal in response.context["page_obj"]]
        self.assertIn(self.animal_adoption, animals_in_page)
        self.assertIn(self.animal_both, animals_in_page)
        # Should not include sponsorship-only animals
        self.assertNotIn(self.animal_sponsorship, animals_in_page)
        # Should not include inactive animals
        self.assertNotIn(self.animal_inactive, animals_in_page)

    def test_sponsorship_list_view(self):
        """Test sponsorship list view"""
        url = reverse("sponsorhip_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "animals/sponsorship.html")

        # Should include animals available for sponsorship (S or B)
        animals_in_page = [animal for animal in response.context["page_obj"]]
        self.assertIn(self.animal_sponsorship, animals_in_page)
        self.assertIn(self.animal_both, animals_in_page)
        # Should not include adoption-only animals
        self.assertNotIn(self.animal_adoption, animals_in_page)

    def test_filter_by_breed(self):
        """Test filtering animals by breed"""
        url = reverse("adoption_list")
        response = self.client.get(url, {"breed": self.breed1.id})

        self.assertEqual(response.status_code, 200)
        animals_in_page = [animal for animal in response.context["page_obj"]]

        # Should only include animals with breed1 (Labrador)
        self.assertIn(self.animal_adoption, animals_in_page)
        self.assertIn(self.animal_both, animals_in_page)

    def test_filter_by_size(self):
        """Test filtering animals by size"""
        url = reverse("adoption_list")
        response = self.client.get(url, {"size": "P"})

        self.assertEqual(response.status_code, 200)
        animals_in_page = [animal for animal in response.context["page_obj"]]

        # Should only include small animals
        self.assertIn(self.animal_both, animals_in_page)  # Size P
        self.assertNotIn(self.animal_adoption, animals_in_page)  # Size G

    def test_filter_by_age_joven(self):
        """Test filtering animals by age (joven: <= 2 years)"""
        url = reverse("adoption_list")
        response = self.client.get(url, {"birth_date": "joven"})

        self.assertEqual(response.status_code, 200)
        # Convert to list to check filtered animals
        animals_in_page = response.context["page_obj"].object_list

        # Luna should be in the list (2 years old)
        # But Luna is only available for sponsorship, not adoption
        # Rocky should NOT be in list (10 years old, senior)
        # Max should NOT be in list (5 years old, adulto)

        # Check that all animals in the list are young (age <= 2)
        for animal in animals_in_page:
            self.assertLessEqual(animal.age, 2)

    def test_filter_by_age_adulto(self):
        """Test filtering animals by age (adulto: 3-7 years)"""
        url = reverse("adoption_list")
        response = self.client.get(url, {"birth_date": "adulto"})

        self.assertEqual(response.status_code, 200)
        animals_in_page = response.context["page_obj"].object_list

        # Max should be in the list (5 years old)
        self.assertIn(self.animal_adoption, animals_in_page)

        # Check that all animals in the list are adults (3 <= age <= 7)
        for animal in animals_in_page:
            self.assertTrue(3 <= animal.age <= 7)

    def test_filter_by_age_senior(self):
        """Test filtering animals by age (senior: >= 8 years)"""
        url = reverse("adoption_list")
        response = self.client.get(url, {"birth_date": "senior"})

        self.assertEqual(response.status_code, 200)
        animals_in_page = response.context["page_obj"].object_list

        # Rocky should be in the list (10 years old)
        self.assertIn(self.animal_both, animals_in_page)

        # Check that all animals in the list are seniors (age >= 8)
        for animal in animals_in_page:
            self.assertGreaterEqual(animal.age, 8)

    def test_pagination(self):
        """Test that pagination works correctly"""
        # Create 10 more animals to test pagination (page size is 8)
        for i in range(10):
            Animal.objects.create(
                name=f"Animal{i}",
                birth_date=date(2020, 1, 1),
                sex="M",
                size="G",
                color="Brown",
                breed=self.breed1,
                shelter=self.shelter,
                availability="A",
                is_active=True,
            )

        url = reverse("adoption_list")
        response = self.client.get(url)

        # Should have pagination
        self.assertTrue("page_obj" in response.context)
        # First page should have 8 animals
        self.assertEqual(len(response.context["page_obj"]), 8)

        # Test page 2
        response_page2 = self.client.get(url, {"page": 2})
        self.assertEqual(response_page2.status_code, 200)
        # Page 2 should have remaining animals
        self.assertGreater(len(response_page2.context["page_obj"]), 0)

    def test_context_data(self):
        """Test that context includes all necessary data"""
        url = reverse("adoption_list")
        response = self.client.get(url, {"breed": self.breed1.id, "size": "G"})

        self.assertEqual(response.status_code, 200)

        # Check context contains breeds
        self.assertIn("breeds", response.context)
        self.assertIn(self.breed1, response.context["breeds"])

        # Check selected filters are in context
        self.assertEqual(response.context["selected_breed"], str(self.breed1.id))
        self.assertEqual(response.context["selected_size"], "G")
        self.assertEqual(response.context["type"], "adoption")


class AnimalDetailViewTestCase(TestCase):
    """Tests for animal detail view"""

    def setUp(self):
        self.client = Client()
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

    def test_animal_detail_view(self):
        """Test animal detail view"""
        url = reverse("animal_detail", args=[self.animal.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "animals/animal_detail.html")
        self.assertEqual(response.context["animal"], self.animal)

    def test_animal_detail_not_found(self):
        """Test animal detail view with non-existent ID"""
        url = reverse("animal_detail", args=[99999])
        response = self.client.get(url)

        # Should return 404
        self.assertEqual(response.status_code, 404)


class AnimalModelTestCase(TestCase):
    """Tests for Animal model methods"""

    def setUp(self):
        self.shelter = Shelter.objects.create(name="Test Shelter", email="shelter@test.com")
        self.breed = Breed.objects.create(name="Labrador", species="C")

    def test_animal_age_property(self):
        """Test that age property calculates correctly"""
        # Create animal born exactly 3 years ago (same month and day)
        today = date.today()
        try:
            three_years_ago = date(today.year - 3, today.month, today.day)
        except ValueError:
            # Handle Feb 29 in non-leap years
            three_years_ago = date(today.year - 3, today.month, today.day - 1)

        animal = Animal.objects.create(
            name="Max",
            birth_date=three_years_ago,
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
        )

        self.assertEqual(animal.age, 3)

    def test_animal_age_property_birthday_not_passed(self):
        """Test age calculation when birthday hasn't passed this year"""
        # Animal born last year but birthday is tomorrow
        tomorrow = date.today() + timedelta(days=1)
        last_year = date(tomorrow.year - 1, tomorrow.month, tomorrow.day)

        animal = Animal.objects.create(
            name="Max",
            birth_date=last_year,
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
        )

        # Should be 0 years old (birthday hasn't passed yet)
        self.assertEqual(animal.age, 0)

    def test_animal_str(self):
        """Test animal string representation"""
        animal = Animal.objects.create(
            name="Max",
            birth_date=date(2020, 1, 1),
            sex="M",
            size="G",
            color="Brown",
            breed=self.breed,
            shelter=self.shelter,
        )

        self.assertEqual(str(animal), f"Max ({self.breed})")
