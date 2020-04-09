from rest_framework import routers

from .views import *


router = routers.DefaultRouter()

# CRUD для счетов
router.register('bills', BillViewSet, basename='bills')
# CRUD для операций
router.register('transactions', TransactionViewSet, basename='transactions')
# CRUD для бюджета
router.register('planned_budget', PlannedBudgetViewSet, basename='planned_budget')
