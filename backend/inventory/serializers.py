
from datetime import date

from rest_framework import serializers

from .models import Medicine


class MedicineSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = [
            "id",
            "name",
            "category",
            "batch_number",
            "manufacturer",
            "quantity",
            "expiry_date",
            "created_at",
            "updated_at",
            "status",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "status"]

    
    def get_status(self, obj):
        from datetime import date

        days_left = (obj.expiry_date - date.today()).days

        if days_left < 0:
            return "Expired"

        warnings = []

        if days_left <= 30:
            warnings.append("Expiring Soon")

        if obj.quantity < 20:
            warnings.append("Low Stock")

        if warnings:
            return ", ".join(warnings)

        return "In Stock"


    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Quantity cannot be negative."
            )
        return value

    def validate_batch_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Batch number cannot be empty."
            )
        return value
