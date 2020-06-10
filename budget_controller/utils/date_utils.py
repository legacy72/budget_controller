from django.utils import timezone


def increase_datetime_now_for_10_minutes():
    return timezone.now() + timezone.timedelta(minutes=10)
