from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.models import Category
from finance.services import ensure_due_salaries, generate_daily_recommendations


class Command(BaseCommand):
    help = "Crea el usuario familiar, categorías e ingresos que correspondan."

    def handle(self, *args, **options):
        User = get_user_model()
        user, _ = User.objects.get_or_create(username="yeison", defaults={"first_name": "Yeison", "is_staff": True})
        if not check_password(settings.APP_PIN, user.password):
            user.set_password(settings.APP_PIN)
            user.save(update_fields=["password"])

        categories = [
            ("Salario", "income", "#3F7D63", "wallet"),
            ("Venta de animales", "income", "#6A9B7F", "piggy-bank"),
            ("Otros ingresos", "income", "#77A98D", "circle-plus"),
            ("Alimentación", "expense", "#E58C6B", "utensils"),
            ("Vivienda", "expense", "#7A89B8", "house"),
            ("Transporte", "expense", "#D4A657", "car"),
            ("Servicios", "expense", "#8D75A5", "receipt"),
            ("Salud", "expense", "#C96C76", "heart-pulse"),
            ("Animales", "expense", "#B27B55", "paw-print"),
            ("Otros gastos", "expense", "#8B8F8C", "circle-ellipsis"),
        ]
        for name, kind, color, icon in categories:
            Category.objects.update_or_create(name=name, kind=kind, defaults={"color": color, "icon": icon, "is_active": True})

        ensure_due_salaries()
        if timezone.localtime().hour >= 12:
            generate_daily_recommendations()
        self.stdout.write(self.style.SUCCESS("Datos iniciales listos."))
