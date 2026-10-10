
from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Medicine


class MedicineAPITests(APITestCase):
    def setUp(self):
        self.list_url = reverse("medicine-list")

        self.medicine = Medicine.objects.create(
            name="Paracetamol",
            category="TABLET",
            batch_number="API-TEST-001",
            manufacturer="Test Pharma",
            quantity=100,
            expiry_date=date.today() + timedelta(days=90),
        )

        self.valid_payload = {
            "name": "Vitamin C",
            "category": "TABLET",
            "batch_number": "API-TEST-002",
            "manufacturer": "Health Pharma",
            "quantity": 50,
            "expiry_date": (
                date.today() + timedelta(days=120)
            ).isoformat(),
        }

    def test_create_medicine(self):
        response = self.client.post(
            self.list_url, self.valid_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medicine.objects.count(), 2)
        self.assertEqual(response.data["name"], "Vitamin C")

    def test_list_medicines(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["name"], "Paracetamol"
        )

    def test_retrieve_medicine(self):
        url = reverse("medicine-detail", args=[self.medicine.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["batch_number"], "API-TEST-001")

    def test_retrieve_missing_medicine_returns_404(self):
        url = reverse("medicine-detail", args=[999999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_medicine_quantity(self):
        url = reverse("medicine-detail", args=[self.medicine.pk])
        response = self.client.patch(
            url, {"quantity": 5}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.quantity, 5)
        self.assertEqual(response.data["status"], "Low Stock")

    def test_delete_medicine(self):
        url = reverse("medicine-detail", args=[self.medicine.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Medicine.objects.filter(pk=self.medicine.pk).exists()
        )

    def test_negative_quantity_is_rejected_by_api(self):
        url = reverse("medicine-detail", args=[self.medicine.pk])
        response = self.client.patch(
            url, {"quantity": -5}, format="json"
        )

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.quantity, 100)

    def test_duplicate_batch_number_is_rejected_by_api(self):
        response = self.client.post(
            self.list_url,
            {
                **self.valid_payload,
                "batch_number": self.medicine.batch_number,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("batch_number", response.data)

    def test_search_by_name(self):
        Medicine.objects.create(
            name="Vitamin D",
            batch_number="API-TEST-003",
            quantity=50,
            expiry_date=date.today() + timedelta(days=100),
        )

        response = self.client.get(
            self.list_url, {"search": "vitamin"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Vitamin D")

    def test_ordering_by_name(self):
        Medicine.objects.create(
            name="Aspirin",
            batch_number="API-TEST-004",
            quantity=50,
            expiry_date=date.today() + timedelta(days=100),
        )

        response = self.client.get(
            self.list_url, {"ordering": "name"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, ["Aspirin", "Paracetamol"])

    def test_pagination(self):
        for i in range(12):
            Medicine.objects.create(
                name=f"Pagination Medicine {i}",
                batch_number=f"PAGE-TEST-{i}",
                quantity=50,
                expiry_date=date.today() + timedelta(days=100 + i),
            )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 13)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
