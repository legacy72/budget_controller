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
# Обновление батча бюджетов
router.register('edit_planned_budgets', EditPlannedBudgetsViewSet, basename='edit_planned_budgets')
# Планирование бюджета по категориям
router.register('balance', BalanceViewSet, basename='balance')
# Бюджет (доход/расход)
router.register('budget', BudgetViewSet, basename='budget')
# Статистика (доход/расход)
router.register('statistic', StatisticViewSet, basename='statistic')
# Активация пользователя по коду
router.register('activate_user', ActivateUserView, basename='activate_user')
# Повторная отправка кода на почту
router.register('resend_code', ResendCodeView, basename='resend_code')
# Отправка кода восстановления пароля на почту пользователя
router.register('send_restore_code', SendRestoreCodeView, basename='send_restore_code')
# Восстановление пароля
router.register('restore_password', RestorePasswordView, basename='restore_password')
# Наиболее часто используемый счет
router.register('most_used_bill', MostUsedBillViewSet, basename='most_used_bill')
# Аналитика по счетам
router.register('bill_analytic', BillAnalyticViewSet, basename='bill_analytic')
# Свободные деньги
router.register('free_money', FreeMoneyViewSet, basename='free_money')
