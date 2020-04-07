import json

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
    Вьюшка для CRUD'a документов юзеров
    """
    serializer_class = BillSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = Bill.objects\
            .filter(user_id=user_id)\
            .all()
        return queryset
