from rest_framework import routers

from .views import *


router = routers.DefaultRouter()

# CRUD для счетов
router.register('bills', BillViewSet, basename='bills')
