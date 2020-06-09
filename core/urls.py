from rest_framework import routers

from .views import *


router = routers.DefaultRouter()

# CRUD для счетов
router.register('bills', BillViewSet, basename='bills')
# CRUD для счетов
router.register('categories', CategoryViewSet, basename='categories')
# CRUD для операций
router.register('transactions', TransactionViewSet, basename='transactions')
# CRUD для бюджета
router.register('planned_budget', PlannedBudgetViewSet, basename='planned_budget')
# Планирование бюджета по категориям
router.register('balance', BalanceViewSet, basename='balance')
# Бюджет (доход/расход)
router.register('budget', BudgetViewSet, basename='budget')
# Активация пользователя по коду
router.register('activate_user', ActivateUserView, basename='activate_user')
# Повторная отправка кода на почту
router.register('resend_code', ResendCodeView, basename='resend_code')
# Наиболее часто используемый счет
router.register('most_used_bill', MostUsedBill, basename='most_used_bill')
