from django.utils import timezone


def increase_datetime_now(days=0, hours=0, minutes=0):
    return timezone.now() + timezone.timedelta(days=days, hours=hours, minutes=minutes)
