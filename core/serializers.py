from rest_framework import serializers, fields

from .models import *


class BillSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Bill
        fields = ('id', 'user', 'name', 'sum', 'created_date')


class CategorySerializer(serializers.ModelSerializer):
    operation_type_name = serializers.StringRelatedField(
        many=False,
        source='operation_type',
        read_only=True,
    )

    class Meta:
        model = Category
        fields = ('id', 'name', 'operation_type', 'operation_type_name')


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    category_name = serializers.StringRelatedField(
        many=False,
        source='category',
        read_only=True,
    )

    class Meta:
        model = Transaction
        fields = ('id', 'bill', 'category', 'category_name', 'sum', 'date', 'tag', 'comment', 'user')


class PlannedBudgetSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    category_name = serializers.StringRelatedField(
        many=False,
        source='category',
        read_only=True,
    )

    class Meta:
        model = PlannedBudget
        fields = ('id', 'category', 'category_name', 'sum', 'user')
