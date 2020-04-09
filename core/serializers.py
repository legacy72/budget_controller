from rest_framework import serializers, fields

from .models import *


class BillSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Bill
        fields = ('id', 'user', 'name', 'sum', 'created_date')


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Transaction
        fields = ('id', 'bill', 'category', 'sum', 'date', 'tag', 'comment', 'user')


class PlannedBudgetSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = PlannedBudget
        fields = ('id', 'category', 'sum', 'date', 'user')
