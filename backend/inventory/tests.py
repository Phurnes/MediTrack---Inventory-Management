
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import Medicine
from .serializers import MedicineSerializer


class MedicineModelTests(TestCase):
    def setUp(self):
        self.medicine = Medicine.objects.create(
            name="Paracetamol",
            category="TABLET",
            batch_number="PCM001",
            manufacturer="Test Pharma",
            quantity=100,
            expiry_date=date.today() + timedelta(days=90),
        )

    def test_medicine_is_created(self):
        self.assertEqual(Medicine.objects.count(), 1)
        self.assertEqual(self.medicine.name, "Paracetamol")

    def test_string_representation(self):
        self.assertEqual(
            str(self.medicine), "Paracetamol - Batch PCM001"
        )

    def test_medicine_ordering_by_expiry(self):
        Medicine.objects.create(
            name="Ibuprofen",
            category="TABLET",
            batch_number="IBU001",
            quantity=50,
            expiry_date=date.today() + timedelta(days=10),
        )

        medicines = list(Medicine.objects.all())
        self.assertEqual(medicines[0].name, "Ibuprofen")


class MedicineSerializerTests(TestCase):
    def make_medicine(self, **overrides):
        data = {
            "name": "Paracetamol",
            "category": "TABLET",
            "batch_number": "PCM001",
            "manufacturer": "Test Pharma",
            "quantity": 100,
            "expiry_date": date.today() + timedelta(days=90),
        }
        data.update(overrides)
        return MedicineSerializer(data=data)

    def test_valid_medicine_data(self):
        serializer = self.make_medicine()
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_negative_quantity_is_rejected(self):
        serializer = self.make_medicine(quantity=-1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_blank_batch_number_is_rejected(self):
        serializer = self.make_medicine(batch_number="   ")
        self.assertFalse(serializer.is_valid())
        self.assertIn("batch_number", serializer.errors)

    def test_duplicate_batch_number_is_rejected(self):
        Medicine.objects.create(
            name="Paracetamol",
            category="TABLET",
            batch_number="PCM001",
            quantity=100,
            expiry_date=date.today() + timedelta(days=90),
        )

        serializer = self.make_medicine()
        self.assertFalse(serializer.is_valid())
        self.assertIn("batch_number", serializer.errors)

    def test_expired_medicine_status(self):
        medicine = Medicine.objects.create(
            name="Expired Medicine",
            category="TABLET",
            batch_number="EXP001",
            quantity=100,
            expiry_date=date.today() - timedelta(days=1),
        )

        result = MedicineSerializer(medicine).data
        self.assertEqual(result["status"], "Expired")

    def test_expiring_soon_status(self):
        medicine = Medicine.objects.create(
            name="Soon Expiring",
            category="TABLET",
            batch_number="SOON001",
            quantity=100,
            expiry_date=date.today() + timedelta(days=30),
        )

        result = MedicineSerializer(medicine).data
        self.assertEqual(result["status"], "Expiring Soon")

    def test_low_stock_status(self):
        medicine = Medicine.objects.create(
            name="Low Stock Medicine",
            category="TABLET",
            batch_number="LOW001",
            quantity=10,
            expiry_date=date.today() + timedelta(days=90),
        )

        result = MedicineSerializer(medicine).data
        self.assertEqual(result["status"], "Low Stock")

    def test_exactly_20_units_is_not_low_stock(self):
        medicine = Medicine.objects.create(
            name="Stock Boundary",
            category="TABLET",
            batch_number="BOUND001",
            quantity=20,
            expiry_date=date.today() + timedelta(days=90),
        )

        result = MedicineSerializer(medicine).data
        self.assertEqual(result["status"], "In Stock")

    
    def test_expiring_soon_and_low_stock_both_reported(self):
        medicine = Medicine.objects.create(
            name="Combined Warning Medicine",
            category="TABLET",
            batch_number="COMBINED001",
            quantity=10,
            expiry_date=date.today() + timedelta(days=15),
        )

        result = MedicineSerializer(medicine).data
        self.assertEqual(
            result["status"],
            "Expiring Soon, Low Stock",
        )

    def test_expired_medicine_keeps_expired_status(self):
        medicine = Medicine.objects.create(
            name="Expired Low Stock Medicine",
            category="TABLET",
            batch_number="EXPIREDLOW001",
            quantity=5,
            expiry_date=date.today() - timedelta(days=1),
        )

        result = MedicineSerializer(medicine).data
        self.assertEqual(result["status"], "Expired")

