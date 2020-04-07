from rest_framework import serializers, fields

from .models import *


class BillSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Bill
        fields = ('id', 'user', 'name', 'sum', 'created_date')
