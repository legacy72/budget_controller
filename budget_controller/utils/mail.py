import logging
from random import randint

from django.conf import settings
from django.core.mail import send_mail


def generate_auth_code():
    """
    Генерация кода для регистрации или восстановления пароля
    :return:
    """
    return randint(10000, 99999)


def send_code(mail, code):
    """
    Отправка кода подтверждения на почту

    :param mail: почта
    :param code: код
    :return:
    """
    subject = 'Регистрация в приложении Budget Keeper'
    message = ' Спасибо за регистрацию. Ваш код подтверждения: {}'.format(code)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [mail]
    try:
        send_mail(subject, message, email_from, recipient_list)
    except Exception as e:
        logging.error(f'Не удалось отправить код на почту. Ошибка: {str(e)}')
        return {'success': False, 'error': str(e)}
    return {'success': True}
