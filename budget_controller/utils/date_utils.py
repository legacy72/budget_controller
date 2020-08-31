from django.utils import timezone


def increase_datetime_now_for_10_minutes():
    return timezone.now() + timezone.timedelta(minutes=10)


def get_last_date():
    """
    Получение последнего дня месяца для date__range фильтра
    """
    return timezone.now().date() + timezone.timedelta(days=1)
