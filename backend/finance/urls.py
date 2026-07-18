from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    AnimalInvestmentViewSet, CategoryViewSet, DashboardView, EggRecordViewSet,
    LogoutView, PinLoginView, ReceiptScanView, RecommendationViewSet, TransactionViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("animals", AnimalInvestmentViewSet, basename="animal")
router.register("eggs", EggRecordViewSet, basename="egg")
router.register("recommendations", RecommendationViewSet, basename="recommendation")

urlpatterns = [
    path("auth/pin/", PinLoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("dashboard/", DashboardView.as_view()),
    path("receipts/scan/", ReceiptScanView.as_view()),
    path("", include(router.urls)),
]
