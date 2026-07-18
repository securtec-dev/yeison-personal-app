from celery import shared_task
from .services import ensure_due_salaries, generate_daily_recommendations


@shared_task(name="finance.tasks.ensure_salaries_task")
def ensure_salaries_task():
    return [item.pk for item in ensure_due_salaries()]


@shared_task(name="finance.tasks.generate_daily_recommendations_task")
def generate_daily_recommendations_task():
    return [item.pk for item in generate_daily_recommendations()]
