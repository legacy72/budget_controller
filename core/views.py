from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils import timezone

from .serializers import *
from .models import (
    Bill, OperationType, Category, Transaction, PlannedBudget
)


@api_view(['POST'])
def registration_view(request):
    """
    Вьюшка для создания пользователя
    По умолчанию пользователю создается нулевой бюджет для каждой категории

    :param request: username - логин
    :param request: email - почта
    :param request: password - пароль
    :param request: repeat_password - повторный пароль для подтверждения
    :return:
    """
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            user = serializer.save()
            categories = Category.objects.all()
            for category in categories:
                planned_budget = PlannedBudget(
                    user=user,
                    category=category,
                    sum=0,
                )
                planned_budget.save()
            data['response'] = 'Пользователь успешно зарегистрирован'
        else:
            data = serializer.errors
        return Response(data)


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


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a категорий
    """
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.all()
        return queryset


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a транзакций
    """
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = Transaction.objects\
            .filter(user_id=user_id, bill__user_id=user_id)\
            .all()
        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        bill = data['bill']
        if self.request.user.id != bill.user_id:
            raise Exception('У пользователя нет такого счета')
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

    :param request: month - месяц в формате числа (1, 2, 3, ...) (если не передан, то берется текущий месяц)
    :param request: year - год в формате числа (2019, 2020, ...) (если не передан, то берется текущий год)
    """
    serializer_class = PlannedBudgetSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')

        queryset = PlannedBudget.objects \
            .select_related('category') \
            .filter(
                user_id=user_id,
                date__month=month if month else timezone.now().month,
                date__year=year if year else timezone.now().year,
            ).all()
        return queryset


class CurrentSituationViewSet(viewsets.ViewSet):
    """
    Вьюшка для бюджета по категориям
    """
    def list(self, request):
        user_id = self.request.user.id

        planned_budget = PlannedBudget.objects.filter(
            user_id=user_id,
            date__month=timezone.now().month,
            date__year=timezone.now().year,
        ).all()

        fact_budget = []
        for planned_budget_by_category in planned_budget:
            transactions_by_category = Transaction.objects.filter(
                user_id=user_id,
                date__month=timezone.now().month,
                date__year=timezone.now().year,
                category_id=planned_budget_by_category.category_id,
            ).all()

            fact_budget_by_category = {
                'category': planned_budget_by_category.category.name,
                'operation_type': planned_budget_by_category.category.operation_type.id,
                'operation_type_name': planned_budget_by_category.category.operation_type.name,
                'planed': planned_budget_by_category.sum,  # сколько планируется заработать/потратить
                'fact': 0,  # сколько по факту заработал/потратил
                'balance': planned_budget_by_category.sum,  # сколько осталось заработать/потратить
            }

            for tranz in transactions_by_category:
                fact_budget_by_category['balance'] -= tranz.sum
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
