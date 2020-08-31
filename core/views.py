import calendar
from collections import Counter

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from url_filter.integrations.drf import DjangoFilterBackend

from .models import (
    User, Bill, Category, Transaction, PlannedBudget, AuthCode
)
from .serializers import (
    UserSerializer, BillSerializer, CategorySerializer, TransactionSerializer, PlannedBudgetSerializer
)
from budget_controller.utils.date_utils import get_last_date
from budget_controller.utils.mail import send_code, generate_auth_code


@api_view(['POST'])
def registration_view(request):
    """
    Вьюшка для создания пользователя
    По умолчанию пользователю создается нулевой бюджет для каждой категории
    Пользователь при создании является неактивным пока не применит код из сообщения на почте

    :param request: email - почта
    :param request: password - пароль
    :param request: repeat_password - повторный пароль для подтверждения
    :return: {
        "email": почта созданного пользователя
    }
    """
    # {
    #     "email": "test@mail.ru",
    #     "password": "test",
    #     "repeat_password": "test"
    # }
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # создание пользователя (неактивным)
            old_user = User.objects.filter(email=serializer.data['email'])
            if old_user:
                return Response(
                    {'Error': 'Пользователь с таким email уже существует'},
                    status=status.HTTP_409_CONFLICT
                )
            user = serializer.save()
            # генерация кода
            code = generate_auth_code()
            # отправка кода подтверждения
            resp = send_code(
                subject='Регистрация в приложении Budget Keeper',
                message=f'Спасибо за регистрацию. Ваш код подтверждения: {code}',
                mail=serializer.data['email'],
            )
            if not resp['success']:
                user.delete()
                return Response({'message': 'Не удалось отправить код'})
            # добавлени кода в базу
            auth_code = AuthCode(user=user, code=code)
            auth_code.save()
            # создание нулевого бюджета по каждой основной категории
            categories = Category.objects.filter(user__isnull=True).all()
            for category in categories:
                planned_budget = PlannedBudget(
                    user=user,
                    category=category,
                    sum=0,
                )
                planned_budget.save()
            data = serializer.data
        else:
            data = serializer.errors
        return Response(data)


class ActivateUserView(viewsets.ViewSet):
    """
    Вьюшка для активации пользователя

    :param request: code - код активации из сообщения на почте
    :param request: username - логин пользователя (равен почте)
    :return:
    """
    def create(self, request):
        data = request.data
        try:
            user = User.objects.get(username=data.get('username'))
        except User.DoesNotExist:
            return Response(
                {'Error': 'Пользователь с данным логином не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )
        auth_code = AuthCode.objects.filter(
            user=user,
            code=data.get('code'),
            end_date__gte=timezone.now(),
        ).all()
        if not auth_code:
            return Response(
                {'Error': 'Код истек или введен неверно'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = True
        user.save()
        return Response({'message': 'Пользователь успешно активирован'})


class ResendCodeView(viewsets.ViewSet):
    """
    Вьюшка для повторной отправки кода на почту пользователя

    :param request: username - логин пользователя (равен почте)
    :return:
    """
    def create(self, request):
        data = request.data
        try:
            user = User.objects.get(username=data.get('username'))
        except User.DoesNotExist:
            return Response(
                {'Error': 'Пользователь с данным логином не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_code, created = AuthCode.objects.get_or_create(user=user)
        # генерация кода
        code = generate_auth_code()
        # отправка кода подтверждения
        resp = send_code(
            subject='Регистрация в приложении Budget Keeper',
            message=f'Спасибо за регистрацию. Ваш код подтверждения: {code}',
            mail=data.get('username'),
        )
        if not resp['success']:
            return Response({'message': 'Не удалось отправить код'})
        auth_code.code = code
        auth_code.end_date = timezone.now() + timezone.timedelta(minutes=10)
        auth_code.save()

        return Response({'message': 'Код успешно отправлен'})


class SendRestoreCodeView(viewsets.ViewSet):
    """
    Вьюшка для отправки кода восстановления пароля на почту пользователя

    :param request: username - логин пользователя (равен почте)
    :return:
    """
    def create(self, request):
        data = request.data
        try:
            user = User.objects.get(username=data.get('username'))
        except User.DoesNotExist:
            return Response(
                {'Error': 'Пользователь с данным логином не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_code, created = AuthCode.objects.get_or_create(user=user)
        # генерация кода
        code = generate_auth_code()
        # отправка кода подтверждения
        resp = send_code(
            subject='Восстановления пароля Budget Keeper',
            message=f'Код для восстановления пароля: {code}',
            mail=data.get('username'),
        )
        if not resp['success']:
            return Response({'message': 'Не удалось отправить код'})
        auth_code.code = code
        auth_code.end_date = timezone.now() + timezone.timedelta(minutes=10)
        auth_code.save()

        return Response({'message': 'Код успешно отправлен'})


class RestorePasswordView(viewsets.ViewSet):
    """
    Вьюшка для восстановления пароля

    :param request: username - логин пользователя (равен почте)
    :param request: code - код активации из сообщения на почте
    :param request: password - пароль
    :param request: repeat_password - повторный пароль для подтверждения
    :return:
    """
    def create(self, request):
        data = request.data
        try:
            user = User.objects.get(username=data.get('username'))
        except User.DoesNotExist:
            return Response(
                {'Error': 'Пользователь с данным логином не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )
        auth_code = AuthCode.objects.filter(
            user=user,
            code=data.get('code'),
            end_date__gte=timezone.now(),
        ).all()
        if not auth_code:
            return Response(
                {'Error': 'Код истек или введен неверно'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if data.get('password') != data.get('repeat_password'):
            return Response(
                {'Error': 'Пароли не совпадают'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(data.get('password'))
        user.save()
        return Response({'message': 'Пароль успешно обновлен'})


class BillViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a счетов текущего пользователя

    Если не указывается дата создания, то ставится текущая по умолчанию
    """
    serializer_class = BillSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filter_fields = ['id', 'user', 'name', 'type', 'sum', 'created_date']

    def get_queryset(self):
        user = self.request.user.id
        queryset = Bill.objects\
            .filter(user=user)\
            .prefetch_related('user')
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a категорий

    Если заходить под анонимым пользователем, то будут показаны основные категории
    Если под конкретным, то основные+личные
    """
    serializer_class = CategorySerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filter_fields = ['id', 'user', 'operation_type', 'name']

    def get_queryset(self):
        user = self.request.user.id
        queryset = Category.objects\
            .select_related('operation_type')\
            .filter(Q(user=user) | Q(user__isnull=True))
        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        category = serializer.save()
        # при создании новой категории добавляем по умолчанию ей нулевой бюджет текущего месяца
        planned_budget = PlannedBudget(
            user=data['user'],
            category=category,
            sum=0,
        )
        planned_budget.save()


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a транзакций

    Если не указывается дата создания, то ставится текущая по умолчанию
    """
    serializer_class = TransactionSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filter_fields = ['id', 'user', 'category', 'bill', 'date', 'sum', 'tag']

    def get_queryset(self):
        user = self.request.user.id
        queryset = Transaction.objects\
            .select_related('bill', 'category', 'category__operation_type')\
            .filter(user=user, bill__user=user)\
            .order_by('date')
        return queryset

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = data['user']
        category_user = data['category'].user
        bill = data['bill']

        if category_user and category_user != user:
            return Response(
                {'Error': 'У Вас нет такой категории'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if self.request.user != bill.user:
            return Response(
                {'Error': 'У Вас нет такого счета'},
                status=status.HTTP_400_BAD_REQUEST
            )

        operation_type = data['category'].operation_type.name
        if operation_type == 'income':
            bill.sum += data['sum']
        elif operation_type == 'expense':
            bill.sum -= data['sum']
        bill.save()

        serializer.save()
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class PlannedBudgetViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a планируемого бюджета
    Если по какой-то из стандартной категории нет бюджета, то создастся автоматически нулевой по ней

    P.S. Для создания день можно указывать любой, учитываться будет только месяц и год

    :param request: month - месяц в формате числа (1, 2, 3, ...) (если не передан, то берется текущий месяц)
    :param request: year - год в формате числа (2019, 2020, ...) (если не передан, то берется текущий год)
    """
    serializer_class = PlannedBudgetSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filter_fields = ['id', 'user', 'category', 'sum', 'date']

    def get_queryset(self):
        user = self.request.user
        month = self.request.query_params.get('month', timezone.now().month)
        year = self.request.query_params.get('year', timezone.now().year)

        # создание нулевого бюджета по каждой основной категории, если его ещё нет
        categories = Category.objects.filter(user__isnull=True).all()
        for category in categories:
            planned_budget = PlannedBudget.objects.filter(
                user=user,
                category=category,
                date__month=month,
                date__year=year,
            )
            if not planned_budget:
                planned_budget = PlannedBudget(
                    user=user,
                    category=category,
                    sum=0,
                )
                planned_budget.save()
        # получение всех планируемых бюджетов
        queryset = PlannedBudget.objects \
            .select_related('category') \
            .filter(
                user=user,
                date__month=month,
                date__year=year,
            )
        return queryset

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        category_user = data['category'].user
        user = data['user']
        if category_user and category_user != user:
            return Response(
                {'Error': 'У Вас нет такой категории'},
                status=status.HTTP_400_BAD_REQUEST
            )
        planned_budget = PlannedBudget.objects \
            .select_related('category') \
            .filter(
                user=user,
                category=data['category'],
                date__month=data['date'].month,
                date__year=data['date'].year,
            ).all()
        if planned_budget:
            return Response(
                {'Error': 'На текущий месяц уже создана данная категория'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class EditPlannedBudgetsViewSet(viewsets.ViewSet):
    """
    Обновление батча планируемых бюджетов POST запросом

    :param request: Массив бюджетов с полями id и sum (новая сумма бюджета), которые нужно обновить
    Пример: [{"id": 14, "sum": "100.00"}, {"id": 13, "sum": "101.00"}]
    """

    def create(self, request):
        new_budgets = request.data
        for new_budget in new_budgets:
            try:
                planned_budget = PlannedBudget.objects.get(id=new_budget['id'])
            except PlannedBudget.DoesNotExist:
                continue
            planned_budget.sum = new_budget['sum']
            planned_budget.save()
        return Response({'message': 'Бюджеты обновлены'}, status=status.HTTP_200_OK)


class BalanceViewSet(viewsets.ViewSet):
    """
    Вьюшка для просмотра текущего состояния бюджета по категориям

    :param request: month - месяц в формате числа (1, 2, 3, ...) (если не передан, то берется текущий месяц)
    :param request: year - год в формате числа (2019, 2020, ...) (если не передан, то берется текущий год)
    
    category - id категории
    category_name - название категории
    operation_type - id типа операции
    operation_type_name - название операции
    planed - планировано было заработать/потратить
    fact - фактически было заработано/потрачено
    balance - остаток (если отрицательный у категории дохода, то значит перерасход, если у прибыли - то заработано
                       больше чем планировалось)
    date - дата (берем отсюда месяц и год)
    """
    def list(self, request):
        user = self.request.user.id
        month = self.request.query_params.get('month', timezone.now().month)
        year = self.request.query_params.get('year', timezone.now().year)

        planned_budget = PlannedBudget.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
        ).select_related('category', 'category__operation_type')

        fact_budget = []
        for planned_budget_by_category in planned_budget:
            transactions_by_category = Transaction.objects.filter(
                user=user,
                date__month=timezone.now().month,
                date__year=timezone.now().year,
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
                'date': planned_budget_by_category.date,
            }

            for tranz in transactions_by_category:
                fact_budget_by_category['balance'] -= tranz.sum
                fact_budget_by_category['fact'] += tranz.sum

            fact_budget.append(fact_budget_by_category)

        return Response(fact_budget)


class BudgetViewSet(viewsets.ViewSet):
    """
    Вьюшка для просмотра всего бюджета за выбранную дату (месяц и год)

    :param request: month - месяц в формате числа (1, 2, 3, ...) (если не передан, то берется текущий месяц)
    :param request: year - год в формате числа (2019, 2020, ...) (если не передан, то берется текущий год)

    plan_income - планируемый доход
    fact_income - фактический дохо
    plan_expense - планирымый расход
    fact_expense - фактический расход
    plan_saving_money - сколько было запланировано сохранить средств
    fact_saving_money - сколько фактически получилось сохранить средств
    money_to_spend - остаток, сколько можно ещё потратить (если число отрициальное, значит вышел за пределы бюджета)
    date - дата
    """
    def list(self, request):
        user = self.request.user.id
        month = self.request.query_params.get('month', timezone.now().month)
        year = self.request.query_params.get('year', timezone.now().year)

        transactions = Transaction.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
        ).select_related('bill', 'category', 'category__operation_type')
        planned_budgets = PlannedBudget.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
        ).select_related('category', 'category__operation_type')

        budget = {
            'plan_income': sum(p.sum for p in planned_budgets if p.category.operation_type.name == 'income'),
            'fact_income': 0,
            'plan_expense': sum(p.sum for p in planned_budgets if p.category.operation_type.name == 'expense'),
            'fact_expense': 0,
            'plan_saving_money': 0,
            'fact_saving_money': 0,
            'money_to_spend': 0,
            'date': planned_budgets[0].date if planned_budgets else None,
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


class StatisticViewSet(viewsets.ViewSet):
    """
    Вьюшка для просмотра cтатистики доходов/расходов за определенный диапазон

    :param request: start_date - начальная дата в формате %Y-%m-%d (день нужно указывать 1)
    :param request: end_date - конечная дата в формате %Y-%m-%d (день нужно указывать последний в текущем месяце)
                               (если не передана, то берется текущая)

    income - доход
    expense - расход
    month - месяц
    year - год
    """
    def list(self, request):
        user = self.request.user.id
        start_date_param = self.request.query_params.get('start_date')
        end_date_param = self.request.query_params.get('end_date')

        if not start_date_param:
            return Response(
                {'Error': 'Не указана начальная дата'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date = timezone.make_aware(timezone.datetime.strptime(start_date_param, "%Y-%m-%d"))
        end_date = timezone.datetime.strptime(end_date_param, "%Y-%m-%d") if end_date_param else get_last_date()

        statistic = []

        transactions = Transaction.objects\
            .filter(
                user=user,
                date__range=(start_date, end_date),  # TODO: DateTimeField Transaction.date received a naive datetime
            )\
            .select_related('bill', 'category', 'category__operation_type')\
            .order_by('date')
        month_statistic = {
            'income': 0,
            'expense': 0,
            'month': int(start_date.month),
            'year': int(start_date.year),
        }
        for transaction in transactions:
            # если новый месяц наступил в списке транзакций, то создаем новый словарь на следующий месяц, а этот месяц
            # записываем в массив
            if transaction.date.month != month_statistic['month'] or transaction.date.year != month_statistic['year']:
                if month_statistic['income'] != 0 or month_statistic['expense'] != 0:
                    statistic.append(month_statistic)
                month_statistic = {
                    'income': 0,
                    'expense': 0,
                    'month': transaction.date.month,
                    'year': transaction.date.year,
                }
            if transaction.category.operation_type.name == 'income':
                month_statistic['income'] += transaction.sum
            if transaction.category.operation_type.name == 'expense':
                month_statistic['expense'] += transaction.sum
        # последний месяц тоже записываем в массив
        statistic.append(month_statistic)
        return Response(statistic)


class MostUsedBillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюшка для получения наиболее часто используемого счета
    """
    serializer_class = BillSerializer

    def get_queryset(self):
        user = self.request.user.id
        transactions = Transaction.objects\
            .filter(user=user)\
            .select_related('bill', 'category', 'category__operation_type')
        bills = [transaction.bill for transaction in transactions]
        counter = Counter(bills)
        bill = counter.most_common(1)
        if not bill:
            return []
        return [bill[0][0]]


class BillAnalyticViewSet(viewsets.ViewSet):
    """
    Вьюшка для просмотра аналитики по счетам

    Последний объект в массиве относится к сумме по всем счетам вместе взятым

    bill - id счета
    bill_name - название счета
    type - тип счета (cash/non_cash)
    income - сколько заработано по счету
    expense - сколько потрачено по счету
    balance - баланс (остаток)

    all_income - сколько всего заработано по счету
    all_expense - сколько всего потрачено по счету
    all_balance - весь баланс (остаток)
    """

    def list(self, request):
        user = self.request.user.id
        bills = Bill.objects\
            .filter(user=user)\
            .prefetch_related('user')

        bills_analytic = []
        all_bills_analytics = {
            'all_income': 0,
            'all_expense': 0,
            'all_balance': 0,
        }
        for bill in bills:
            bill_analytic = {
                'bill': bill.id,
                'bill_name': bill.name,
                'type': bill.type,
                'income': 0,
                'expense': 0,
                'balance': bill.sum,
            }
            transactions = Transaction.objects.filter(
                user=user,
                bill=bill,
            ).select_related('bill', 'category', 'category__operation_type')
            for transaction in transactions:
                if transaction.category.operation_type.name == 'income':
                    bill_analytic['income'] += transaction.sum
                    all_bills_analytics['all_income'] += transaction.sum
                if transaction.category.operation_type.name == 'expense':
                    bill_analytic['expense'] += transaction.sum
                    all_bills_analytics['all_expense'] += transaction.sum
            bills_analytic.append(bill_analytic)
        # баланс по всем счетам вместе взятым
        all_bills_analytics['all_balance'] = all_bills_analytics['all_income'] - all_bills_analytics['all_expense']
        bills_analytic.append(all_bills_analytics)
        return Response(bills_analytic)


class FreeMoneyViewSet(viewsets.ViewSet):
    """
    Вьюшка для просмотра свободных денег на текущий день/неделю/месяц

    free_money_for_day - свободные деньги на день
    free_money_for_week - свободные деньги на неделю
    free_money_for_month - свободные деньги на месяц
    """
    def list(self, request):
        user = self.request.user.id
        month = timezone.now().month
        year = timezone.now().year

        transactions = Transaction.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
        ).select_related('bill', 'category', 'category__operation_type')
        planned_budgets = PlannedBudget.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
        ).select_related('category', 'category__operation_type')

        budget = {
            'free_money_for_day': 0,
            'free_money_for_week': 0,
            'free_money_for_month': 0,
        }

        plan_income = sum(p.sum for p in planned_budgets if p.category.operation_type.name == 'income')
        fact_income = 0
        plan_expense = sum(p.sum for p in planned_budgets if p.category.operation_type.name == 'expense')
        fact_expense = 0
        
        for transaction in transactions:
            if transaction.category.operation_type.name == 'income':
                fact_income += transaction.sum
            if transaction.category.operation_type.name == 'expense':
                fact_expense += transaction.sum

        fact_saving_money = fact_income - fact_expense
        plan_saving_money = plan_income - plan_expense

        # дней до конца текущего месяца
        days_for_end_month = calendar.monthrange(year, month)[1] - timezone.now().day
        # если это последний день, то считаем, что остался ещё один день вместо 0
        days_for_end_month = days_for_end_month if days_for_end_month else 1
        # номер текущей недели
        number_of_current_week = timezone.now().day // 7 + 1

        budget['free_money_for_day'] = (fact_saving_money - plan_saving_money) // days_for_end_month
        budget['free_money_for_week'] = (fact_saving_money - plan_saving_money) // 4 * number_of_current_week
        budget['free_money_for_month'] = fact_saving_money - plan_saving_money

        return Response(budget)
