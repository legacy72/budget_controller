from django.utils import timezone


def increase_datetime_now_for_10_minutes():
    return timezone.now() + timezone.timedelta(minutes=10)


def get_last_date():
    """
    Получение последнего дня месяца для date__range фильтра
    """
    current_datetime = timezone.now() + timezone.timedelta(days=1)
    return current_datetime.replace(hour=0, minute=0, second=0)
