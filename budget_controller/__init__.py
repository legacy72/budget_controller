from .settings import *

try:
    from .local_settings import *
except ImportError:
    print('Ошибка с локальными настройками')
