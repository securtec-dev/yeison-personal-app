from django.contrib import admin
from .models import AnimalInvestment, AuditLog, Category, EggRecord, FinancialTransaction, Receipt, Recommendation

admin.site.register([Category, Receipt, FinancialTransaction, AnimalInvestment, EggRecord, Recommendation, AuditLog])
