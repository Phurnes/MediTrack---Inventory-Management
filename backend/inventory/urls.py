
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MedicineViewSet, stock_planner

router = DefaultRouter()
router.register("medicines", MedicineViewSet, basename="medicine")

urlpatterns = [
    path("", include(router.urls)),
    path("planner/", stock_planner, name="stock-planner"),
]
