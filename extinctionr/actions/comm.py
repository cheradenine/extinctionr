from enum import Enum
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mass_mail, get_connection
from django.utils.timezone import now, localtime
from django.utils import dateformat
from django.template import Engine, Context
from .models import Action, Attendee

from extinctionr.utils import base_url
from extinctionr.circles import get_circle

logger = logging.getLogger(__name__)

MESSAGE = """
Hi {name},

You said you'd commit to attending "{action_name}" if at least {num} people also committed.
We've now got enough other folks to commit! We hope to see you there, on {action_date}.
More details here: {action_url}

Solidarity,
Extinction Rebellion Massachusetts

P.S. If you can't make it, please get in touch. We're all in this together.

"""


def notify_commitments(action, threshold, action_url):
    """
    Send notification email to all attendees who agreed to commit if at least 'threshold'
    number of others commit.
    Will not send notifications for actions which have already happened.
    Will not notify attendees twice.
    """
    if now() > action.when:
        return 0
    attendees = action.attendee_set.filter(
        promised__isnull=False, mutual_commitment=0
    ) | action.attendee_set.filter(mutual_commitment__lte=threshold)
    if attendees.count() >= threshold:
        to_send = attendees.filter(notified=None, mutual_commitment__gt=0)
        subject = "[XR] We've got enough to commit to %s" % action.name
        messages = []
        modified = set()
        from_email = settings.NOREPLY_FROM_EMAIL
        when = dateformat.format(localtime(action.when), "l, F jS @ g:iA")
        for attendee in to_send:
            if attendee in modified:
                continue
            full_name = "%s %s" % (
                attendee.contact.first_name,
                attendee.contact.last_name,
            )
            msg = MESSAGE.format(
                name=full_name,
                action_name=action.name,
                action_date=when,
                action_url=action_url,
                num=attendee.mutual_commitment,
            )
            messages.append((subject, msg, from_email, [attendee.contact.email]))
            attendee.notified = now()
            if not attendee.promised:
                attendee.promised = now()
            modified.add(attendee)
        send_mass_mail(messages)
        for attendee in modified:
            attendee.save()
        return len(messages)


def _render_action_email(action, attendee, outreach_email, template):
    if isinstance(template, str):
        template = Engine.get_default().get_template(template)

    ctx = {
        "action": action,
        "contact": attendee.contact,
        "base_url": base_url(),
        "outreach_email": outreach_email,
    }
    msg_body = template.render(Context(ctx))

    return msg_body


def _check_attendee_whitelist(attendee):
    whitelist = settings.ACTION_RSVP_WHITELIST
    if "*" in whitelist:
        return True
    return attendee.contact.email in whitelist


class EventReminder(Enum):
    RSVP = 0
    NEXT_DAY = 1
    SOON = 2


def confirm_rsvp(action, attendee, ics_data):
    """
    Send notification email to attendee when they register.
    Will not send notifications for actions which have already happened.
    Will not notify attendees twice.
    """
    if now() > (action.when - timedelta(hours=2)):
        return

    if not _check_attendee_whitelist(attendee):
        return

    # Prevents getting a reminder too soon.
    attendee.notified = now()

    outreach = get_circle("outreach")

    if not outreach:
        logger.warning("Outreach circle not found. App is misconfigured and will not send mail.")
        return 0

    from_email = settings.NOREPLY_FROM_EMAIL
    subject = "[XR Boston] RSVP confirmation for {}".format(action.text_title)
    msg_body_html = _render_action_email(
        action, attendee, outreach.public_email, "action_email_rsvp.html"
    )
    msg_body_plain = _render_action_email(
        action, attendee, outreach.public_email, "action_email_rsvp.txt"
    )

    msg = EmailMultiAlternatives(
        subject, msg_body_plain, from_email, [attendee.contact.email]
    )
    msg.attach_alternative(msg_body_html, "text/html")
    msg.attach(f"{action.slug}.ics", ics_data, "text/calendar")
    msg.send()

    attendee.save()




def send_action_reminder(action, attendees, reminder):
    
    engine = Engine.get_default()

    if reminder is EventReminder.NEXT_DAY:
        template_html = engine.get_template("action_email_reminder_day.html")
        template_plain = engine.get_template("action_email_reminder_day.txt")
        subject = "[XR Boston] Event reminder: {} is coming up".format(
            action.text_title
        )
    elif reminder is EventReminder.SOON:
        template_html = engine.get_template("action_email_reminder_soon.html")
        template_plain = engine.get_template("action_email_reminder_soon.txt")
        subject = "[XR Boston] Event reminder: {} is startng soon".format(
            action.text_title
        )
    else:
        raise ValueError("Unknown reminder type")

    from_email = settings.NOREPLY_FROM_EMAIL
    outreach = get_circle("outreach")

    if not outreach:
        logger.warning("Outreach circle not found. App is misconfigured and will not send mail.")
        return 0

    notified = set()
    messages = []

    # Can't use send_mass_mail because it doesn't work with html
    mail_connection = get_connection()

    time_now = now()

    for attendee in attendees:
        if attendee in notified:
            continue
        if not _check_attendee_whitelist(attendee):
            continue
        # If they got a reminder less than one day ago, skip this one.
        if attendee.notified and time_now < (attendee.notified + timedelta(days=1)):
            continue
        notified.add(attendee)
        msg_body_plain = _render_action_email(action, attendee, outreach.public_email, template_plain)
        msg_body_html = _render_action_email(action, attendee, outreach.public_email, template_html)
        msg = EmailMultiAlternatives(subject, msg_body_plain, from_email, [attendee.contact.email], connection=mail_connection)
        msg.attach_alternative(msg_body_html, "text/html")
        messages.append(msg)
        # Record when they were notified so that we don't do it again right away.
        attendee.notified = time_now

    mail_connection.send_messages(messages)
    
    for attendee in notified:
        attendee.save()

    return len(notified)
