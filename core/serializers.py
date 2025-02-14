from rest_framework import serializers, fields

from .models import *


class UserSerializer(serializers.ModelSerializer):
    repeat_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'repeat_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self):
        user = User(
            username=self.validated_data['email'],
            email=self.validated_data['email'],
            is_active=False,
        )
        password = self.validated_data['password']
        repeat_password = self.validated_data['repeat_password']
        if password != repeat_password:
            raise serializers.ValidationError({'password': 'Пароли не совпадают'})
        user.set_password(password)
        user.save()
        return user


class BillSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Bill
        fields = ('id', 'user', 'name', 'type', 'sum', 'created_date')


class CategorySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )
    operation_type_name = serializers.StringRelatedField(
        many=False,
        source='operation_type',
        read_only=True,
    )

    class Meta:
        model = Category
        fields = ('id', 'user', 'name', 'operation_type', 'operation_type_name', 'code_name')


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )
    category_name = serializers.StringRelatedField(
        many=False,
        source='category',
        read_only=True,
    )
    bill_name = serializers.StringRelatedField(
        many=False,
        source='bill',
        read_only=True,
    )
    bill_type = serializers.SerializerMethodField(method_name='get_bill_type')

    operation_type = serializers.SerializerMethodField(method_name='get_operation_type')
    operation_type_name = serializers.SerializerMethodField(method_name='get_operation_type_name')

    class Meta:
        model = Transaction
        fields = ('id', 'bill', 'bill_name', 'bill_type', 'category', 'category_name', 'operation_type',
                  'operation_type_name', 'sum', 'date', 'tag', 'comment', 'user')

    def get_bill_type(self, obj):
        return obj.bill.type

    def get_operation_type(self, obj):
        return obj.category.operation_type.id

    def get_operation_type_name(self, obj):
        return obj.category.operation_type.name


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
        fields = ('id', 'category', 'category_name', 'sum', 'date', 'user')
