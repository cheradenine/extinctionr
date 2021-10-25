from django.conf import settings
from django.core.mail import send_mass_mail, send_mail
from extinctionr.utils import base_url

from .models import Contact
from extinctionr.circles import get_circle


def notify_circle_membership(circle, msg_type, members):
    addresses = circle.get_notification_addresses()
    contacts = Contact.objects.filter(pk__in=members)
    context = {
        'contact': str(contacts[0]),
        'contact_email': contacts[0].email,
        'circle': str(circle),
        'circle_url': '%s%s' % (base_url(), circle.get_absolute_url()),
    }
    if msg_type == 'pending member':
        context['action'] = 'wants to join'
    else:
        context['action'] = 'joined'
    message = '''
{contact} <{contact_email}> {action} {circle}

{circle_url}#members
'''.format(**context)
    subject = '[XR] %s added to %s' % (msg_type, circle)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, addresses)


def notify_circle_job(job):
    circle = job.circle
    addresses = circle.get_notification_addresses()
    addresses.add(job.creator.email)
    subject = '[XR] Job filled by {}'.format(job.filled)
    title = job.title or job.id
    message = '''{who} has signed up to fill job "{title}" in {circle}

{job}

{baseurl}{url}
'''.format(who=job.filled, title=title, circle=circle, job=job.job, baseurl=base_url(), url=job.get_absolute_url())
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, addresses)


def notify_new_volunteer(volunteer):
    contact = volunteer.contact
    outreach_circle = get_circle('outreach')
    subject = '[XR] New Volunteer Request: {}'.format(contact)
    message = '''{who} <{email}> has signed up to volunteer.

View all new requests at:
  {baseurl}/admin/circles/volunteerrequest/?status__exact=n

Edit this request at:
  {baseurl}/admin/circles/volunteerrequest/edit/{pk}/

'''.format(who=contact, email=contact.email, baseurl=base_url(), pk=volunteer.id)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, outreach_circle.get_notification_addresses())
