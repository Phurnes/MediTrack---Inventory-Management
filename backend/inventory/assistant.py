
import json
import logging
import os
from datetime import date, timedelta

from django.db.models import Count, Sum
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Medicine
from .planner import generate_stock_plan


logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RESULTS = 50

CATEGORIES = [
    "TABLET",
    "CAPSULE",
    "SYRUP",
    "INJECTION",
    "OINTMENT",
    "DROPS",
    "OTHER",
]

ALLOWED_ACTIONS = {
    "inventory_summary",
    "expiring_medicines",
    "expired_medicines",
    "low_stock",
    "stock_at_risk",
}


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=api_key)


def interpret_question(client, question):
    """Interpret a question as a restricted inventory operation."""
    today = date.today()

    prompt = f"""
You are the intent parser for MediTrack AI Assistant.
Today's date is {today.isoformat()}.

Choose exactly one action:
- inventory_summary: overall inventory statistics and problems
- expiring_medicines: medicines expiring today or in a future date window
- expired_medicines: medicines whose expiry date is before today
- low_stock: medicines with quantity below a specified threshold
- stock_at_risk: inventory grouped by category, focusing on expired,
  expiring, or low-stock records

Return ONLY a JSON object with these fields:
{{
  "action": "one allowed action",
  "days": 30,
  "min_quantity": 20,
  "category": ""
}}

Rules:
- days must be an integer from 0 to 365.
- min_quantity must be an integer from 0 to 1000000.
- category must be one of {CATEGORIES}, or an empty string.
- Use 30 days by default for expiry-window questions.
- Use 20 as the default low-stock threshold.
- For expired medicines with quantities above 50, use
  expired_medicines and set min_quantity to 51.
- Never generate SQL or request unrestricted database access.
- If unrelated to inventory, use inventory_summary.

User question:
{question}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    parsed = json.loads(response.text or "{}")
    action = parsed.get("action")

    if action not in ALLOWED_ACTIONS:
        raise ValueError("Unsupported inventory operation.")

    days = parsed.get("days", 30)
    threshold = parsed.get("min_quantity", 20)
    category = parsed.get("category", "")

    if not isinstance(days, int) or isinstance(days, bool):
        days = 30

    if not isinstance(threshold, int) or isinstance(threshold, bool):
        threshold = 20

    days = max(0, min(days, 365))
    threshold = max(0, min(threshold, 1_000_000))

    if category not in CATEGORIES:
        category = ""

    return {
        "action": action,
        "days": days,
        "min_quantity": threshold,
        "category": category,
    }


def medicine_data(queryset):
    """Return a limited set of actual inventory records."""
    return [
        {
            "name": item.name,
            "category": item.category,
            "batch_number": item.batch_number,
            "quantity": item.quantity,
            "expiry_date": item.expiry_date.isoformat(),
            "manufacturer": item.manufacturer,
        }
        for item in queryset.order_by("expiry_date", "name")[:MAX_RESULTS]
    ]


def run_inventory_tool(intent):
    """Run predefined, read-only inventory queries using Django ORM."""
    today = date.today()
    action = intent["action"]
    days = intent["days"]
    threshold = intent["min_quantity"]
    category = intent["category"]

    medicines = Medicine.objects.all()

    if category:
        medicines = medicines.filter(category=category)

    if action == "inventory_summary":
        expired = medicines.filter(expiry_date__lt=today)

        expiring = medicines.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30),
        )

        low_stock = medicines.filter(quantity__lt=20)

        return {
            "action": action,
            "as_of": today.isoformat(),
            "total_records": medicines.count(),
            "total_units": medicines.aggregate(
                total=Sum("quantity")
            )["total"] or 0,
            "expired_count": expired.count(),
            "expired_units": expired.aggregate(
                total=Sum("quantity")
            )["total"] or 0,
            "expiring_within_30_days_count": expiring.count(),
            "expiring_within_30_days_units": expiring.aggregate(
                total=Sum("quantity")
            )["total"] or 0,
            "low_stock_count": low_stock.count(),
            "low_stock_threshold": 20,
        }

    if action == "expiring_medicines":
        queryset = medicines.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=days),
        )

        count = queryset.count()

        return {
            "action": action,
            "as_of": today.isoformat(),
            "window_days": days,
            "count": count,
            "total_units": queryset.aggregate(
                total=Sum("quantity")
            )["total"] or 0,
            "records": medicine_data(queryset),
            "truncated": count > MAX_RESULTS,
        }

    if action == "expired_medicines":
        queryset = medicines.filter(
            expiry_date__lt=today,
            quantity__gte=threshold,
        )

        count = queryset.count()

        return {
            "action": action,
            "as_of": today.isoformat(),
            "minimum_quantity": threshold,
            "count": count,
            "total_units": queryset.aggregate(
                total=Sum("quantity")
            )["total"] or 0,
            "records": medicine_data(queryset),
            "truncated": count > MAX_RESULTS,
        }

    if action == "low_stock":
        queryset = medicines.filter(quantity__lt=threshold)
        count = queryset.count()

        return {
            "action": action,
            "as_of": today.isoformat(),
            "threshold": threshold,
            "count": count,
            "records": medicine_data(queryset),
            "truncated": count > MAX_RESULTS,
        }

    if action == "stock_at_risk":
        at_risk = medicines.filter(
            expiry_date__lte=today + timedelta(days=30)
        )

        category_summary = list(
            at_risk.values("category")
            .annotate(
                medicine_count=Count("id"),
                total_units=Sum("quantity"),
            )
            .order_by("-total_units")
        )

        low_stock = medicines.filter(quantity__lt=20)
        count = at_risk.count()

        return {
            "action": action,
            "as_of": today.isoformat(),
            "expiry_window_days": 30,
            "at_risk_medicine_count": count,
            "at_risk_units": at_risk.aggregate(
                total=Sum("quantity")
            )["total"] or 0,
            "at_risk_by_category": category_summary,
            "low_stock_count": low_stock.count(),
            "low_stock_threshold": 20,
            "records": medicine_data(at_risk),
            "truncated": count > MAX_RESULTS,
        }

    raise ValueError("Unsupported inventory operation.")


def explain_results(client, question, results):
    """Explain verified database results without inventing facts."""
    prompt = f"""
You are MediTrack AI Assistant, an inventory reporting assistant.

Answer the user's question using ONLY the database results below.

Rules:
- Do not invent medicine names, quantities, dates, or statistics.
- Preserve numerical values supplied by the database.
- Explain relevant findings clearly and concisely.
- If no matching records exist, say so.
- Mention if the returned record list is truncated.
- Distinguish expired medicines from medicines expiring in the future.
- Do not provide medical treatment advice.
- State any limitations in the available data.
- When action is stock_plan, explain only the calculated planner results.
- The suggested order is already calculated as max(0, target stock - usable stock).
- Do not recalculate, alter, or invent suggested quantities.
- Expired batches are excluded from usable stock; report expiring batches separately.
- This planner uses target stock, not historical consumption or demand forecasting.

User question:
{question}

Verified database results:
{json.dumps(results, ensure_ascii=False)}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )

    answer = (response.text or "").strip()

    if not answer:
        raise RuntimeError("The AI provider returned an empty answer.")

    return answer


@api_view(["POST"])
@permission_classes([AllowAny])
def assistant_chat(request):
    question = request.data.get("question", "")

    if not isinstance(question, str):
        return Response(
            {"error": "Question must be text."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    question = question.strip()

    if not question:
        return Response(
            {"error": "Please enter a question."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(question) > 1000:
        return Response(
            {"error": "Question must be 1000 characters or fewer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = get_gemini_client()

        planner_keywords = (
            "stock plan",
            "stock planner",
            "suggested order",
            "how many units",
            "reorder",
            "restock",
            "target stock",
            "order quantity",
        )

        is_planner_question = any(
            keyword in question.casefold()
            for keyword in planner_keywords
        )

        if is_planner_question:
            results = generate_stock_plan()
            results["action"] = "stock_plan"
        else:
            intent = interpret_question(client, question)
            results = run_inventory_tool(intent)

        answer = explain_results(client, question, results)

        return Response({
            "answer": answer,
            "data": results,
        })

    except (ValueError, json.JSONDecodeError):
        return Response(
            {
                "error": (
                    "I couldn't interpret that question. Please rephrase it."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        logger.exception("MediTrack AI Assistant request failed.")

        return Response(
            {
                "error": (
                    "The assistant could not complete the request. "
                    "Check the Django terminal for details."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
