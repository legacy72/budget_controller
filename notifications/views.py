from collections import Counter

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from url_filter.integrations.drf import DjangoFilterBackend

from core.models import (
    User, Bill, Category, Transaction, PlannedBudget, AuthCode
)
from budget_controller.utils.money import round_money


class ReduceExpenseViewSet(viewsets.ViewSet):
    """
    Mock
    """

    def list(self, request):
        return Response(True)


class AverageDeviationViewSet(viewsets.ViewSet):
    """
    Mock
    """

    def list(self, request):
        # TODO: в данной реализации не учитываются месяцы, в которых не было совершенно тарнзакций (возможно стоит)
        user = self.request.user.id

        statistic = []

        transactions = Transaction.objects\
            .filter(
                user=user,
            )\
            .select_related('bill', 'category', 'category__operation_type')\
            .order_by('date')
        month_statistic = {
            'income': 0,
            'expense': 0,
            'month': transactions[0].date.month,
            'year': transactions[0].date.year,
        }
        income = 0
        expense = 0
        count_months = 0
        for transaction in transactions:
            # если новый месяц наступил в списке транзакций, то создаем новый словарь на следующий месяц, а этот месяц
            # записываем в массив
            if transaction.date.month != month_statistic['month'] or transaction.date.year != month_statistic['year']:
                statistic.append(month_statistic)
                month_statistic = {
                    'income': 0,
                    'expense': 0,
                    'month': transaction.date.month,
                    'year': transaction.date.year,
                }
                count_months += 1

            if transaction.category.operation_type.name == 'income':
                month_statistic['income'] += transaction.sum
                income += transaction.sum
            if transaction.category.operation_type.name == 'expense':
                month_statistic['expense'] += transaction.sum
                expense += transaction.sum
        # последний месяц тоже записываем в массив
        statistic.append(month_statistic)
        count_months += 1

        average_deviation = {
            'average_income': round_money(income / count_months),
            'average_expense': round_money(expense / count_months),
        }

        return Response(average_deviation)


class BudgetExpirationViewSet(viewsets.ViewSet):
    """
    Mock
    """

    def list(self, request):
        return Response(True)
