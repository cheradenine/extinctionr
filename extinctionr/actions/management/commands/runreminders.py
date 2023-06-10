import logging
from datetime import timedelta
import asyncio

from asgiref.sync import sync_to_async

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.timezone import now, localtime
from django.utils import dateformat

from extinctionr.actions.models import Action, Attendee
from extinctionr.actions.comm import EventReminder, send_action_reminder


logger = logging.getLogger(__name__)


def _upcoming_actions(time_now, hours):
    start = time_now + timedelta(hours=hours, minutes=-30)
    end = time_now + timedelta(hours=hours, minutes=30)
    return Action.objects.filter(when__range=(start, end))


@sync_to_async
def _send_reminders(hours, reminder_type):
    time_now = now()
    actions = _upcoming_actions(time_now, hours)
    actions = actions.filter(Q(send_reminders__isnull=True) | Q(send_reminders=True))


    logger.info("checking reminders for %s", reminder_type)
    action_count = actions.count()
    logger.info("found %d action%s", action_count, "" if action_count == 1 else "s")

    notification_cutoff = time_now - timedelta(days=1)
    logger.info("notifying attendees that haven't been notified since %s", notification_cutoff)

    for action in actions:

        # Filter actions that don't have reminders set.
        if not action.send_reminders:
            continue

        attendees = (
            Attendee.objects.filter(action=action)
            .filter(Q(notified__isnull=True) | Q(notified__lte=notification_cutoff))
            .select_related("contact")
        )

        if attendees.count() > 0:
            logger.info('Will attempt to notify %d attendees', attendees.count())
            sent = send_action_reminder(action, attendees, reminder_type)
            if sent > 0:
                logger.info(
                    "Sent %d %s for %s at %s",
                    sent,
                    "reminder" if sent == 1 else "reminders",
                    action.text_title,
                    dateformat.format(localtime(time_now), "l, F jS @ g:iA"),
                )
        else:
            logger.info("There were no attendees to notify")


async def run_reminders():
    logger.info("Starting reminders service")
    while True:
        # Sleep for 30 mins
        sleep_time = 30 * 60
        await asyncio.sleep(sleep_time)
        await _send_reminders(26, EventReminder.NEXT_DAY)
        await _send_reminders(2, EventReminder.SOON)


class Command(BaseCommand):
    help = "Runs asyncio scheduler for action reminders."

    def handle(self, *args, **options):
        asyncio.run(run_reminders())
