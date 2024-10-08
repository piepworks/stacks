from django.core.mail import send_mail
from config.settings import ADMIN_EMAIL_FROM, ADMIN_EMAIL_TO


def send_email_to_admin(subject, message):
    send_mail(
        subject=subject,
        message=message,
        from_email=f"{ADMIN_EMAIL_FROM}",
        recipient_list=[f"{ADMIN_EMAIL_TO}"],
    )


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def pluralize(noun, count):
    if count != 1:
        return noun + "s"
    return noun
