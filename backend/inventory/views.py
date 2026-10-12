
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Medicine
from .serializers import MedicineSerializer
from .planner import generate_stock_plan


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [AllowAny]

    search_fields = [
        "name",
        "batch_number",
        "manufacturer",
    ]

    ordering_fields = [
        "name",
        "expiry_date",
        "quantity",
        "target_stock",
        "created_at",
    ]

    ordering = ["expiry_date", "name"]


@api_view(["GET"])
def stock_planner(request):
    return Response(generate_stock_plan())
