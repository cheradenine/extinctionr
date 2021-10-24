import logging
from datetime import timedelta
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.timezone import now, localtime, localdate
from django.utils import dateformat

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from extinctionr.actions.models import Action, Attendee
from extinctionr.actions.comm import EventReminder, send_action_reminder


logger = logging.getLogger(__name__)


def _upcoming_actions(time_now, hours):
    start = time_now + timedelta(hours=hours, minutes=-30)
    end = time_now + timedelta(hours=hours, minutes=30)
    return Action.objects.filter(when__date__range=(start, end))


def _send_reminders(hours, reminder_type):
    time_now = now()
    actions = _upcoming_actions(time_now, hours)

    logger.info("checking reminders for %s", reminder_type)

    for action in actions:

        attendees = (
            Attendee.objects.filter(action=action)
            .filter(Q(notified__isnull=True) | Q(notified__lte=time_now - timedelta(days=1)))
            .select_related("contact")
        )

        if attendees.count() > 0:
            logger.info('Will attempt to notify %d attendees', attendees.count())
            sent = send_action_reminder(action, attendees, reminder_type)
            if sent > 0:
                logger.info(
                    "Sent %d %s for %s at %s",
                    "reminder" if sent == 1 else "reminders",
                    sent,
                    action.text_title,
                    dateformat.format(localtime(time_now), "l, F jS @ g:iA"),
                )


def action_reminders_job():
    _send_reminders(26, EventReminder.NEXT_DAY)
    _send_reminders(2, EventReminder.SOON)


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after our job has run.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler for action reminders."

    def handle(self, *args, **options):

        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            action_reminders_job,
#            trigger=CronTrigger(minute="*/30"),  # Every 30 minutes
            trigger=CronTrigger(second="*/10"),
            id="send_action_reminders",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'send_action_reminders'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added weekly job: 'delete_old_job_executions'.")

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
