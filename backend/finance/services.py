import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from django.conf import settings
from django.db import transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import AuditLog, Category, FinancialTransaction, Recommendation


SALARY_AMOUNT = Decimal("180000.00")


@transaction.atomic
def ensure_salaries(target_date=None):
    target_date = target_date or timezone.localdate()
    if target_date.day not in (15, 28):
        return []

    category = Category.objects.get_or_create(
        name="Salario", kind=Category.Kind.INCOME,
        defaults={"color": "#3F7D63", "icon": "wallet"},
    )[0]
    created_items = []
    for person in ("Yeison", "Camila"):
        item, created = FinancialTransaction.objects.get_or_create(
            idempotency_key=f"salary-{person.lower()}-{target_date.isoformat()}",
            defaults={
                "transaction_type": FinancialTransaction.Type.INCOME,
                "amount": SALARY_AMOUNT,
                "description": f"Salario de {person}",
                "date": target_date,
                "category": category,
                "status": FinancialTransaction.Status.COMPLETED,
                "source": FinancialTransaction.Source.SALARY,
            },
        )
        if created:
            AuditLog.objects.create(action="auto_created", entity_type="transaction", entity_id=str(item.pk), details={"source": "salary"})
            created_items.append(item)
    return created_items


def ensure_due_salaries(today=None):
    today = today or timezone.localdate()
    created = []
    for day in (15, 28):
        if today.day >= day:
            created.extend(ensure_salaries(today.replace(day=day)))
    return created


def _parse_amount(value):
    cleaned = re.sub(r"[^0-9,.]", "", value)
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        tail = cleaned.split(",")[-1]
        cleaned = cleaned.replace(",", "." if len(tail) == 2 else "")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def scan_receipt_image(image_path):
    with Image.open(image_path) as original:
        image = ImageOps.exif_transpose(original).convert("L")
        image = ImageEnhance.Contrast(image).enhance(1.8)
        image = image.filter(ImageFilter.SHARPEN)
        text = pytesseract.image_to_string(image, lang="spa", config="--psm 6")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    merchant = lines[0][:150] if lines else ""

    receipt_date = None
    date_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", text)
    if date_match:
        day, month, year = map(int, date_match.groups())
        year = year + 2000 if year < 100 else year
        try:
            receipt_date = date(year, month, day)
        except ValueError:
            pass

    total = None
    total_patterns = [
        r"(?:total\s+a\s+pagar|gran\s+total|total)\s*[:₡$]?\s*([\d.,]+)",
        r"(?:importe|monto)\s*[:₡$]?\s*([\d.,]+)",
    ]
    for pattern in total_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            total = _parse_amount(matches[-1])
            if total:
                break

    confidence = (35 if merchant else 0) + (35 if total else 0) + (30 if receipt_date else 0)
    return {
        "raw_text": text,
        "merchant": merchant,
        "receipt_date": receipt_date,
        "total": total,
        "confidence": confidence,
    }


def _financial_context(today):
    start = today.replace(day=1)
    completed = FinancialTransaction.objects.filter(date__gte=start, date__lte=today, status=FinancialTransaction.Status.COMPLETED)
    zero = Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))
    totals = completed.values("transaction_type").annotate(total=Coalesce(Sum("amount"), zero))
    by_type = {row["transaction_type"]: row["total"] for row in totals}
    categories = list(
        completed.filter(transaction_type=FinancialTransaction.Type.EXPENSE)
        .values("category__name").annotate(total=Sum("amount")).order_by("-total")[:8]
    )
    recent = list(completed.filter(transaction_type=FinancialTransaction.Type.EXPENSE).values("description", "amount", "date")[:15])
    return {
        "period": start.isoformat(),
        "income": str(by_type.get(FinancialTransaction.Type.INCOME, 0)),
        "expenses": str(by_type.get(FinancialTransaction.Type.EXPENSE, 0)),
        "categories": [{"name": row["category__name"] or "Sin categoría", "total": str(row["total"])} for row in categories],
        "recent_expenses": [{"description": row["description"], "amount": str(row["amount"]), "date": row["date"].isoformat()} for row in recent],
    }


def _local_recommendations(context):
    income = Decimal(context["income"])
    expenses = Decimal(context["expenses"])
    items = []
    if income and expenses > income * Decimal("0.75"):
        items.append(("alert", "Ya utilizaste más del 75% de los ingresos del mes. Revisa los gastos no esenciales antes de realizar nuevas compras."))
    for category in context["categories"][:2]:
        name = category["name"]
        total = category["total"]
        items.append(("category", f"{name} suma ₡{Decimal(total):,.0f} este mes. Revisa los movimientos de esta categoría para identificar un ahorro sencillo."))
    if not items:
        items.append(("general", "Registra cada gasto, incluso los pequeños. Con más información podré darte recomendaciones familiares más precisas."))
    if income > expenses:
        items.append(("positive", f"Hasta hoy conservas ₡{income - expenses:,.0f} de tus ingresos del mes. Considera separar una parte antes del próximo pago."))
    return items[:5]


def _claude_recommendations(context):
    if not settings.CLAUDE_API_KEY:
        return None
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=900,
            temperature=0.2,
            system=(
                "Eres un asistente financiero familiar prudente de Costa Rica. Devuelve únicamente JSON válido: "
                "una lista de hasta 5 objetos con claves kind y content. Cada content debe tener máximo 300 caracteres. "
                "Usa colones, sé respetuoso, específico y no inventes datos. No des asesoría financiera riesgosa."
            ),
            messages=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        )
        raw = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(raw)
        valid = []
        for item in parsed[:5]:
            content = str(item.get("content", "")).strip()[:300]
            if content:
                valid.append((str(item.get("kind", "general"))[:30], content))
        return valid or None
    except Exception:
        return None


@transaction.atomic
def generate_daily_recommendations(target_date=None):
    target_date = target_date or timezone.localdate()
    existing = list(Recommendation.objects.filter(date=target_date)[:5])
    if existing:
        return existing
    context = _financial_context(target_date)
    recommendations = _claude_recommendations(context) or _local_recommendations(context)
    return [Recommendation.objects.create(date=target_date, kind=kind, content=content[:300]) for kind, content in recommendations[:5]]
