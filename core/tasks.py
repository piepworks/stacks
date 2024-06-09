from model_bakery import baker
from .models import User

from celery import shared_task
from celery.utils.log import get_task_logger

logging = get_task_logger(__name__)


@shared_task
def import_from_goodreads():
    pass


@shared_task
def create_random_user_accounts(total):
    for i in range(total):
        baker.make(User)
    return "{} random users created with success!".format(total)
