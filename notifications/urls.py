from rest_framework import routers

from .views import *


router = routers.DefaultRouter()

# Уведомление, что нужно сбавить расходы, если в этом есть необходимость
router.register('reduce_expense', ReduceExpenseViewSet, 'reduce_expense')
# Уведомление, которое показывает сколько процентов отклонение от средних расходов и средних заработков
router.register('average_deviation', AverageDeviationViewSet, 'average_deviation')
# Уведомление о том, что по какой-либо категории скоро закончится бюджет
router.register('budget_expiration', BudgetExpirationViewSet, 'budget_expiration')
