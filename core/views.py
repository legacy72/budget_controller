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
    # "email": "test@mail.ru",
    # "password": "test",
    # "repeat_password ": "test"
    # }
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            # создание пользователя (неактивным)
            old_user = User.objects.filter(email=serializer.data['email'])
            if old_user:
                return Response({'error': 'Пользователь с таким email уже существует'})
            user = serializer.save()
            # генерация кода
            code = generate_auth_code()
            # отправка кода подтверждения
            send_code(mail=serializer.data['email'], code=code)
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
            return Response({'error': 'Пользователь с данным логином не найден'})
        auth_code = AuthCode.objects.filter(
            user=user,
            code=data.get('code'),
            end_date__gte=timezone.now(),
        ).all()
        if not auth_code:
            return Response({
                'error': 'Код истек или введен неверно'
            })
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
            return Response({'error': 'Пользователь с данным логином не найден'})

        auth_code, created = AuthCode.objects.get_or_create(user=user)
        # генерация кода
        code = generate_auth_code()
        # отправка кода подтверждения
        send_code(mail=data.get('username'), code=code)
        auth_code.code = code
        auth_code.save()

        return Response({'message': 'Код успешно отправлен'})


class BillViewSet(viewsets.ModelViewSet):
    """
    Вьюшка для CRUD'a счетов текущего пользователя

    Если не указывается дата создания, то ставится текущая по умолчанию
    """
    serializer_class = BillSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filter_fields = ['id', 'user', 'name', 'sum', 'created_date']

    def get_queryset(self):
        user = self.request.user.id
        queryset = Bill.objects\
            .filter(user=user)\
            .all()
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
            .filter(Q(user=user) | Q(user__isnull=True))\
            .all()
        return queryset


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
            .filter(user=user, bill__user=user)\
            .all()
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
                {'Error': 'У Вас нет такой категории'}, status=status.HTTP_400_BAD_REQUEST
            )

        if self.request.user != bill.user:
            return Response(
                {'Error': 'У Вас нет такого счета'}, status=status.HTTP_400_BAD_REQUEST
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

    P.S. Для создания день можно указывать любой, учитываться будет только месяц и год

    :param request: month - месяц в формате числа (1, 2, 3, ...) (если не передан, то берется текущий месяц)
    :param request: year - год в формате числа (2019, 2020, ...) (если не передан, то берется текущий год)
    """
    serializer_class = PlannedBudgetSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filter_fields = ['id', 'user', 'category', 'sum', 'date']

    def get_queryset(self):
        user = self.request.user.id
        month = self.request.query_params.get('month', timezone.now().month)
        year = self.request.query_params.get('year', timezone.now().year)

        queryset = PlannedBudget.objects \
            .select_related('category') \
            .filter(
                user=user,
                date__month=month,
                date__year=year,
            ).all()
        return queryset

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        category_user = data['category'].user
        user = data['user']
        if category_user and category_user != user:
            return Response(
                {'Error': 'У Вас нет такой категории'}, status=status.HTTP_400_BAD_REQUEST
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
                {'Error': 'На текущий месяц уже создана данная категория'}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


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
    """
    def list(self, request):
        user = self.request.user.id
        month = self.request.query_params.get('month', timezone.now().month)
        year = self.request.query_params.get('year', timezone.now().year)

        planned_budget = PlannedBudget.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
        ).all()

        fact_budget = []
        for planned_budget_by_category in planned_budget:
            transactions_by_category = Transaction.objects.filter(
                user=user,
                date__month=timezone.now().month,
                date__year=timezone.now().year,
                category_id=planned_budget_by_category.category_id,
            ).all()

            fact_budget_by_category = {
                'category': planned_budget_by_category.category.id,
                'category_name': planned_budget_by_category.category.name,
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
    Вьюшка для просмотра всего бюджета в текущем месяце

    plan_income - планируемый доход
    fact_income - фактический дохо
    plan_expense - планирымый расход
    fact_expense - фактический расход
    plan_saving_money - сколько было запланировано сохранить средств
    fact_saving_money - сколько фактически получилось сохранить средств
    money_to_spend - остаток, сколько можно ещё потратить (если число отрициальное, значит вышел за пределы бюджета)
    """
    def list(self, request):
        user = self.request.user.id
        transactions = Transaction.objects.filter(
            user=user,
            date__year=timezone.now().year,
            date__month=timezone.now().month,
        ).all()
        planned_budgets = PlannedBudget.objects.filter(
            user=user,
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
