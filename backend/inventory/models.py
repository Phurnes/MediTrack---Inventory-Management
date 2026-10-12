
from django.db import models


class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ("TABLET", "Tablet"),
        ("CAPSULE", "Capsule"),
        ("SYRUP", "Syrup"),
        ("INJECTION", "Injection"),
        ("OINTMENT", "Ointment"),
        ("DROPS", "Drops"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=150, db_index=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="OTHER",
    )
    batch_number = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=150, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    # Desired stock level used by the Smart Stock Planner.
    target_stock = models.PositiveIntegerField(default=20)

    expiry_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "name"]

    def __str__(self):
        return f"{self.name} - Batch {self.batch_number}"
