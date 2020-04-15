import json
from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.response import Response

from .serializers import *
from .models import *


class BillViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a счетов юзеров
    """
    serializer_class = BillSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = Bill.objects\
            .filter(user_id=user_id)\
            .all()
        return queryset


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a транзакций
    """
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = Transaction.objects\
            .filter(user_id=user_id)\
            .all()
        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        bill = data['bill']
        operation_type = data['category'].operation_type.name
        if operation_type == 'income':
            bill.sum += data['sum']
        elif operation_type == 'expense':
            bill.sum -= data['sum']
        bill.save()
        serializer.save()


class PlannedBudgetViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a бюджета
    """
    serializer_class = PlannedBudgetSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = PlannedBudget.objects\
            .filter(user_id=user_id)\
            .all()
        return queryset


class CurrentSituationViewSet(viewsets.ViewSet):
    """
    Вьюшка для бюджета по категориям
    """
    def list(self, request):
        user_id = self.request.user.id

        planned_budget = PlannedBudget.objects.filter(
            user_id=user_id,
            date__month__gte=timezone.now().month,
        ).all()

        fact_budget = []
        for planned_budget_by_category in planned_budget:
            transactions_by_category = Transaction.objects.filter(
                user_id=user_id,
                date__year=timezone.now().year,
                date__month=timezone.now().month,
                category_id=planned_budget_by_category.category_id,
            ).all()

            fact_budget_by_category = {
                'category': planned_budget_by_category.category.name,
                'planed': planned_budget_by_category.sum,  # сколько планируется заработать/потратить
                'fact': 0,  # сколько по факту заработал/потратил
                'need/can': planned_budget_by_category.sum,  # сколько осталось заработать/потратить
            }

            for tranz in transactions_by_category:
                fact_budget_by_category['need/can'] -= tranz.sum
                fact_budget_by_category['fact'] += tranz.sum

            fact_budget.append(fact_budget_by_category)

        return Response(fact_budget)


class BudgetViewSet(viewsets.ViewSet):
    """
    Вьюшка для всего бюджета
    """
    def list(self, request):
        user_id = self.request.user.id
        transactions = Transaction.objects.filter(
            user_id=user_id,
            date__year=timezone.now().year,
            date__month=timezone.now().month,
        ).all()
        planned_budgets = PlannedBudget.objects.filter(
            user_id=user_id,
            date__month__gte=timezone.now().month,
        ).all()

        budget = {
            'plan_income': sum(p.sum for p in planned_budgets if p.category.operation_type.name == 'income'),
            'fact_income': 0,
            'plan_expense': sum(p.sum for p in planned_budgets if p.category.operation_type.name == 'expense'),
            'fact_expense': 0,
            'plan_saving_money': 0,
            'fact_saving_money': 0,
            'money_to_spend': 0,
        }
        for transaction in transactions:
            if transaction.category.operation_type.name == 'income':
                budget['fact_income'] += transaction.sum
            if transaction.category.operation_type.name == 'expense':
                budget['fact_expense'] += transaction.sum

        budget['fact_saving_money'] = budget['fact_income'] - budget['fact_expense']
        budget['plan_saving_money'] = budget['plan_income'] - budget['plan_expense']
        budget['money_to_spend'] = budget['fact_saving_money'] - budget['plan_saving_money']

        return Response(budget)
