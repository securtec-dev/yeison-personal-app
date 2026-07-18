import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Category, FinancialTransaction
from .services import ensure_salaries


class FinanceApiTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="yeison", password="2580")
        token = Token.objects.create(user=user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self.category = Category.objects.create(name="Alimentación", kind="expense")

    def test_idempotent_transaction_creation(self):
        key = str(uuid.uuid4())
        payload = {"transaction_type": "expense", "amount": "3500", "description": "Comida", "date": "2026-07-18", "category_id": self.category.pk}
        first = self.client.post("/api/v1/transactions/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key)
        second = self.client.post("/api/v1/transactions/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(FinancialTransaction.objects.count(), 1)

    def test_salary_job_does_not_duplicate_income(self):
        target = date(2026, 7, 15)
        ensure_salaries(target)
        ensure_salaries(target)
        salaries = FinancialTransaction.objects.filter(source="salary")
        self.assertEqual(salaries.count(), 2)
        self.assertEqual(salaries.aggregate_total if hasattr(salaries, "aggregate_total") else sum(x.amount for x in salaries), Decimal("360000.00"))
