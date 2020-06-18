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
        return Response(True)


class BudgetExpirationViewSet(viewsets.ViewSet):
    """
    Mock
    """

    def list(self, request):
        return Response(True)
