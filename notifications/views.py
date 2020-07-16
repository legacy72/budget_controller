from django.utils import timezone
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from core.models import (
    Transaction, PlannedBudget
)
from budget_controller.utils.money import round_digit


class ReduceExpenseViewSet(viewsets.ViewSet):
    """
    Вьюшка для уведомлений, которые показывают что нужно сбавить расходы, если текущие расходы превышают средний
    показатель

    need_reduce_costs - нужно ли сбавить расходы (true/false)
    expense_deviation_percentage - процент отклонения от среднего расхода
                                   (если число положительное, то отклонение в плюс, если отрицательное - то в минус)
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

        if not transactions:
            return Response(
                {'Error': 'Пока не было совершено ни одной транзакции'},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        average_expense = round_digit(expense / count_months)

        average_deviation = {
            'need_reduce_costs': True if int(100 - average_expense * 100 / month_statistic['expense']) > 0 else False,
            'expense_deviation_percentage': int(100 - average_expense * 100 / month_statistic['expense']),
        }

        return Response(average_deviation)


class AverageDeviationViewSet(viewsets.ViewSet):
    """
    Вьюшка для уведомлений, которые показывают процент отклонения от средних расходов и средних заработков
    P.S. Для полей income_deviation_percentage и expense_deviation_percentage работает правило - если число
    положительное, то отклонение в плюс, если отрицательное - то в минус

    average_income - средний расход
    average_expense - средний доход
    current_income - текущий доход
    current_expense - текущий расход
    income_deviation_percentage - процент отклонения от среднего дохода
    expense_deviation_percentage - процент отклонения от среднего расхода
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

        if not transactions:
            return Response(
                {'Error': 'Пока не было совершено ни одной транзакции'},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        average_income = round_digit(income / count_months)
        average_expense = round_digit(expense / count_months)

        average_deviation = {
            'average_income': average_income,
            'average_expense': average_expense,
            'current_income': month_statistic['income'],
            'current_expense': month_statistic['expense'],
            'income_deviation_percentage': round_digit(100 - average_income * 100 / month_statistic['income']),
            'expense_deviation_percentage': round_digit(100 - average_expense * 100 / month_statistic['expense']),
        }

        return Response(average_deviation)


class BudgetExpirationViewSet(viewsets.ViewSet):
    """
    Уведомление о том, что по какой-либо категории скоро закончится бюджет.
    Определеятся это так: если процент остатка от планируемого бюджета меньше 10 процентов и больше 0, то значит, что
    бюджет скоро закончится по данной категории
    
    category - id категории
    category_name - название категории
    operation_type - id типа операции
    operation_type_name - название операции
    planed - планировано было заработать/потратить
    fact - фактически было заработано/потрачено
    balance - остаток (если отрицательный у категории дохода, то значит перерасход, если у прибыли - то заработано
                       больше чем планировалось)
    balance_percent - процент оставшейся суммы от планируемого бюджета
    soon_expiration - истечет ли скоро бюджет (true/false)
    """

    def list(self, request):
        user = self.request.user.id
        month = timezone.now().month
        year = timezone.now().year

        planned_budget = PlannedBudget.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
            category__operation_type__name='expense',
        ).select_related('category', 'category__operation_type')

        fact_budget = []
        for planned_budget_by_category in planned_budget:
            transactions_by_category = Transaction.objects.filter(
                user=user,
                date__month=month,
                date__year=year,
                category_id=planned_budget_by_category.category_id,
            ).select_related('bill', 'category', 'category__operation_type')

            fact_budget_by_category = {
                'category': planned_budget_by_category.category.id,
                'category_name': planned_budget_by_category.category.name,
                'operation_type': planned_budget_by_category.category.operation_type.id,
                'operation_type_name': planned_budget_by_category.category.operation_type.name,
                'planed': planned_budget_by_category.sum,  # сколько планируется заработать/потратить
                'fact': 0,  # сколько по факту заработал/потратил
                'balance': planned_budget_by_category.sum,  # сколько осталось заработать/потратить
                'balance_percent': 0,  # сколько осталось от планируемого бюджета в процентах
                'soon_expiration': False,
            }

            for tranz in transactions_by_category:
                fact_budget_by_category['balance'] -= tranz.sum
                fact_budget_by_category['fact'] += tranz.sum

            # если планирумый бюджет не 0 (избегаем деление на 0), то считаем процент оставшейся суммы от план. бюджета
            if fact_budget_by_category['planed']:
                fact_budget_by_category['balance_percent'] = round_digit(
                    fact_budget_by_category['balance'] / fact_budget_by_category['planed'] * 100
                )

            # если процент остатка от планируемого бюджета меньше 10 процентов и больше 0, то значит, что
            # бюджет скоро закончится по данной категории
            if 0 < fact_budget_by_category['balance_percent'] < 10:
                fact_budget_by_category['soon_expiration'] = True

            fact_budget.append(fact_budget_by_category)

        return Response(fact_budget)
