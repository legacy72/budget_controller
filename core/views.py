import json
from decimal import Decimal

from django.core.validators import validate_email
from django.utils.html import strip_tags
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.renderers import StaticHTMLRenderer

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
    Вьюшка для CRUD'a счетов юзеров
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
    Вьюшка для CRUD'a счетов юзеров
    """
    serializer_class = PlannedBudgetSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = PlannedBudget.objects\
            .filter(user_id=user_id)\
            .all()
        return queryset
