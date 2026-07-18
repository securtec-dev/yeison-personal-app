import uuid
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.Model):
    class Kind(models.TextChoices):
        INCOME = "income", "Ingreso"
        EXPENSE = "expense", "Gasto"

    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    color = models.CharField(max_length=7, default="#3F7D63")
    icon = models.CharField(max_length=32, default="circle")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["kind", "name"]
        constraints = [models.UniqueConstraint(fields=["name", "kind"], name="unique_category_kind")]

    def __str__(self):
        return self.name


class Receipt(models.Model):
    class Status(models.TextChoices):
        SCANNED = "scanned", "Escaneada"
        LINKED = "linked", "Guardada"
        DISCARDED = "discarded", "Descartada"

    image = models.ImageField(upload_to="receipts/%Y/%m/")
    raw_text = models.TextField(blank=True)
    merchant = models.CharField(max_length=150, blank=True)
    receipt_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    confidence = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCANNED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class FinancialTransaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income", "Ingreso"
        EXPENSE = "expense", "Gasto"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        SALARY = "salary", "Salario automático"
        RECEIPT = "receipt", "Factura"
        ANIMAL = "animal", "Animales"

    transaction_type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    description = models.CharField(max_length=180)
    date = models.DateField()
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="transactions")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.COMPLETED)
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.MANUAL)
    idempotency_key = models.CharField(max_length=128, unique=True, default=uuid.uuid4, editable=False)
    receipt = models.OneToOneField(Receipt, null=True, blank=True, on_delete=models.SET_NULL, related_name="transaction")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["transaction_type", "date"]),
        ]

    def __str__(self):
        return f"{self.description}: {self.amount}"


class AnimalInvestment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        SOLD = "sold", "Vendida"

    name = models.CharField(max_length=120, default="Inversión general de animales")
    purchase_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    purchase_date = models.DateField()
    sale_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    sale_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-purchase_date", "-created_at"]
        indexes = [models.Index(fields=["status", "purchase_date"])]

    @property
    def profit(self):
        if self.sale_amount is None:
            return None
        return self.sale_amount - self.purchase_amount


class EggRecord(models.Model):
    date = models.DateField(unique=True)
    quantity = models.PositiveIntegerField(validators=[MaxValueValidator(10000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]


class Recommendation(models.Model):
    date = models.DateField()
    content = models.CharField(max_length=300)
    kind = models.CharField(max_length=30, default="general")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "created_at"]
        constraints = [models.UniqueConstraint(fields=["date", "content"], name="unique_daily_recommendation")]


class AuditLog(models.Model):
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["entity_type", "entity_id"])]
