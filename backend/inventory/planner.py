
from collections import defaultdict
from datetime import date, timedelta

from .models import Medicine


def generate_stock_plan():
    """Calculate replenishment suggestions grouped by medicine name/category."""
    today = date.today()
    warning_date = today + timedelta(days=30)

    grouped = defaultdict(
        lambda: {
            "name": "",
            "category": "",
            "manufacturer": "",
            "target_stock": 0,
            "usable_stock": 0,
            "expired_stock": 0,
            "expiring_soon_stock": 0,
            "expiring_soon_batches": 0,
            "batches": [],
        }
    )

    for medicine in Medicine.objects.all().order_by(
        "name", "expiry_date"
    ):
        key = (
            medicine.name.strip().casefold(),
            medicine.category,
        )

        item = grouped[key]

        item["name"] = medicine.name
        item["category"] = medicine.category
        item["manufacturer"] = medicine.manufacturer

        # If batch targets differ, use the highest target temporarily.
        item["target_stock"] = max(
            item["target_stock"],
            medicine.target_stock,
        )

        batch = {
            "batch_number": medicine.batch_number,
            "quantity": medicine.quantity,
            "expiry_date": medicine.expiry_date.isoformat(),
            "status": "Usable",
        }

        if medicine.expiry_date < today:
            item["expired_stock"] += medicine.quantity
            batch["status"] = "Expired"
        else:
            item["usable_stock"] += medicine.quantity

            if medicine.expiry_date <= warning_date:
                item["expiring_soon_stock"] += medicine.quantity
                item["expiring_soon_batches"] += 1
                batch["status"] = "Expiring Soon"

        item["batches"].append(batch)

    plan = []

    for item in grouped.values():
        item["suggested_order"] = max(
            0,
            item["target_stock"] - item["usable_stock"],
        )

        if item["usable_stock"] == 0:
            item["priority"] = "Critical"
        elif item["suggested_order"] > 0:
            item["priority"] = "Reorder"
        elif item["expiring_soon_batches"] > 0:
            item["priority"] = "Review Expiry"
        else:
            item["priority"] = "Sufficient"

        plan.append(item)

    priority_order = {
        "Critical": 0,
        "Reorder": 1,
        "Review Expiry": 2,
        "Sufficient": 3,
    }

    plan.sort(
        key=lambda item: (
            priority_order[item["priority"]],
            item["name"].casefold(),
        )
    )

    return {
        "generated_on": today.isoformat(),
        "total_medicines": len(plan),
        "medicines_to_reorder": sum(
            1 for item in plan if item["suggested_order"] > 0
        ),
        "total_suggested_units": sum(
            item["suggested_order"] for item in plan
        ),
        "items": plan,
    }
