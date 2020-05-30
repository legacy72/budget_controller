from .settings import *

try:
    from .local_settings import *
except ImportError:
    print('Локальные настройки не импортированы')
