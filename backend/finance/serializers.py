from rest_framework import serializers
from .models import AnimalInvestment, Category, EggRecord, FinancialTransaction, Receipt, Recommendation


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "kind", "color", "icon"]


class ReceiptSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = ["id", "image_url", "raw_text", "merchant", "receipt_date", "total", "confidence", "status", "created_at"]
        read_only_fields = fields

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class FinancialTransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.filter(is_active=True), allow_null=True, required=False, write_only=True
    )
    receipt_id = serializers.PrimaryKeyRelatedField(
        source="receipt", queryset=Receipt.objects.filter(status=Receipt.Status.SCANNED), allow_null=True, required=False, write_only=True
    )
    receipt = ReceiptSerializer(read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = [
            "id", "transaction_type", "amount", "description", "date", "category", "category_id",
            "status", "source", "idempotency_key", "receipt", "receipt_id", "note", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "idempotency_key", "created_at", "updated_at"]

    def validate(self, attrs):
        category = attrs.get("category")
        transaction_type = attrs.get("transaction_type", getattr(self.instance, "transaction_type", None))
        if category and category.kind != transaction_type:
            raise serializers.ValidationError({"category_id": "La categoría no corresponde al tipo de movimiento."})
        return attrs


class AnimalInvestmentSerializer(serializers.ModelSerializer):
    profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = AnimalInvestment
        fields = [
            "id", "name", "purchase_amount", "purchase_date", "sale_amount", "sale_date",
            "status", "profit", "note", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "profit", "created_at", "updated_at"]

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", AnimalInvestment.Status.ACTIVE))
        sale_amount = attrs.get("sale_amount", getattr(self.instance, "sale_amount", None))
        sale_date = attrs.get("sale_date", getattr(self.instance, "sale_date", None))
        if status == AnimalInvestment.Status.SOLD and (sale_amount is None or sale_date is None):
            raise serializers.ValidationError("Para completar una venta debes indicar el monto y la fecha de venta.")
        return attrs


class EggRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EggRecord
        fields = ["id", "date", "quantity", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ["id", "date", "content", "kind", "created_at"]
        read_only_fields = fields
