import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError, transaction
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import AnimalInvestment, AuditLog, Category, EggRecord, FinancialTransaction, Receipt, Recommendation
from .serializers import (
    AnimalInvestmentSerializer, CategorySerializer, EggRecordSerializer,
    FinancialTransactionSerializer, ReceiptSerializer, RecommendationSerializer,
)
from .services import ensure_due_salaries, generate_daily_recommendations, scan_receipt_image


class PinLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "pin_login"

    def post(self, request):
        pin = str(request.data.get("pin", ""))
        if len(pin) != 4 or not pin.isdigit():
            return Response({"detail": "El PIN debe contener 4 dígitos."}, status=status.HTTP_400_BAD_REQUEST)
        User = get_user_model()
        try:
            user = User.objects.get(username="yeison", is_active=True)
        except User.DoesNotExist:
            return Response({"detail": "El acceso aún no está configurado."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not check_password(pin, user.password):
            return Response({"detail": "PIN incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "name": "Yeison", "household": "Casa Yeison"})


class LogoutView(APIView):
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialTransactionSerializer
    parser_classes = [JSONParser]

    def get_queryset(self):
        queryset = FinancialTransaction.objects.select_related("category", "receipt")
        transaction_type = self.request.query_params.get("type")
        if transaction_type in FinancialTransaction.Type.values:
            queryset = queryset.filter(transaction_type=transaction_type)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        key = request.headers.get("Idempotency-Key", "").strip()[:128] or str(uuid.uuid4())
        existing = self.get_queryset().filter(idempotency_key=key).first()
        if existing:
            response = Response(self.get_serializer(existing).data, status=status.HTTP_200_OK)
            response["X-Idempotent-Replayed"] = "true"
            return response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = serializer.save(idempotency_key=key)
        except IntegrityError:
            item = self.get_queryset().get(idempotency_key=key)
            response = Response(self.get_serializer(item).data, status=status.HTTP_200_OK)
            response["X-Idempotent-Replayed"] = "true"
            return response
        if item.receipt_id:
            Receipt.objects.filter(pk=item.receipt_id).update(status=Receipt.Status.LINKED)
        AuditLog.objects.create(action="created", entity_type="transaction", entity_id=str(item.pk), details={"idempotency_key": key})
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def perform_update(self, serializer):
        item = serializer.save()
        AuditLog.objects.create(action="updated", entity_type="transaction", entity_id=str(item.pk))

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        item.status = FinancialTransaction.Status.CANCELLED
        item.save(update_fields=["status", "updated_at"])
        AuditLog.objects.create(action="cancelled", entity_type="transaction", entity_id=str(item.pk))
        return Response(self.get_serializer(item).data)


class AnimalInvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = AnimalInvestmentSerializer
    queryset = AnimalInvestment.objects.all()

    @transaction.atomic
    def perform_create(self, serializer):
        item = serializer.save()
        AuditLog.objects.create(action="created", entity_type="animal_investment", entity_id=str(item.pk))

    @transaction.atomic
    def perform_update(self, serializer):
        item = serializer.save()
        AuditLog.objects.create(action="updated", entity_type="animal_investment", entity_id=str(item.pk))


class EggRecordViewSet(viewsets.ModelViewSet):
    serializer_class = EggRecordSerializer
    queryset = EggRecord.objects.all()


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecommendationSerializer

    def get_queryset(self):
        return Recommendation.objects.filter(date=timezone.localdate())[:5]

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        items = generate_daily_recommendations()
        return Response(self.get_serializer(items, many=True).data)


class ReceiptScanView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "receipt_scan"

    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "Selecciona una fotografía de la factura."}, status=status.HTTP_400_BAD_REQUEST)
        if image.size > 8 * 1024 * 1024:
            return Response({"detail": "La imagen no puede superar 8 MB."}, status=status.HTTP_400_BAD_REQUEST)
        if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
            return Response({"detail": "Usa una imagen JPG, PNG o WebP."}, status=status.HTTP_400_BAD_REQUEST)
        receipt = Receipt.objects.create(image=image)
        try:
            result = scan_receipt_image(receipt.image.path)
        except Exception:
            result = {"raw_text": "", "merchant": "", "receipt_date": None, "total": None, "confidence": 0}
        for field, value in result.items():
            setattr(receipt, field, value)
        receipt.save(update_fields=["raw_text", "merchant", "receipt_date", "total", "confidence"])
        return Response(ReceiptSerializer(receipt, context={"request": request}).data, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    def get(self, request):
        today = timezone.localdate()
        ensure_due_salaries(today)
        start = today.replace(day=1)
        zero = Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))
        completed = FinancialTransaction.objects.filter(date__gte=start, date__lte=today, status=FinancialTransaction.Status.COMPLETED)
        income = completed.filter(transaction_type=FinancialTransaction.Type.INCOME).aggregate(value=Coalesce(Sum("amount"), zero))["value"]
        expenses = completed.filter(transaction_type=FinancialTransaction.Type.EXPENSE).aggregate(value=Coalesce(Sum("amount"), zero))["value"]
        animal_stats = AnimalInvestment.objects.aggregate(
            invested=Coalesce(Sum("purchase_amount"), zero),
            sold=Coalesce(Sum("sale_amount"), zero),
        )
        recent = FinancialTransactionSerializer(
            FinancialTransaction.objects.select_related("category", "receipt")[:5], many=True, context={"request": request}
        ).data
        recommendations = Recommendation.objects.filter(date=today)[:5]
        next_payday = 15 if today.day < 15 else 28 if today.day < 28 else 15
        next_month = today.month if today.day < 28 else (today.month % 12) + 1
        next_year = today.year if today.day < 28 or today.month < 12 else today.year + 1
        return Response({
            "today": today,
            "month": {"income": income, "expenses": expenses, "balance": income - expenses},
            "animals": {"invested": animal_stats["invested"], "sold": animal_stats["sold"], "profit": animal_stats["sold"] - animal_stats["invested"]},
            "eggs_today": EggRecord.objects.filter(date=today).values_list("quantity", flat=True).first() or 0,
            "next_income": {"date": f"{next_year:04d}-{next_month:02d}-{next_payday:02d}", "amount": Decimal("360000.00")},
            "recent_transactions": recent,
            "recommendations": RecommendationSerializer(recommendations, many=True).data,
        })
