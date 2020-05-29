import datetime
from hashlib import md5
from urllib.parse import quote

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.timezone import now
from django.utils.safestring import mark_safe
from django.utils.html import linebreaks

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel
)
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.models import Orderable


from markdownx.models import MarkdownxField
from markdown import markdown
from taggit.managers import TaggableManager

from contacts.models import Contact

from extinctionr.info.models import Photo
from extinctionr.utils import get_contact


USER_MODEL = get_user_model()

class ActionManager(models.Manager):
    def for_user(self, user):
        qset = self.all().order_by('when')
        if user.is_anonymous:
            qset = qset.filter(public=True)
        if not user.is_staff:
            qset = qset.exclude(tags__name='pending')
        return qset

class Action(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    when = models.DateTimeField(db_index=True)
    description = MarkdownxField(default='', blank=True, help_text='Markdown formatted')
    slug = models.SlugField(unique=True, help_text='Short form of the title, for URLs')
    public = models.BooleanField(default=True, blank=True, help_text='Whether this action should be listed publicly')
    location = models.TextField(default='', blank=True, help_text='Event location will be converted to a google maps link, unless you format it as a Markdown link -- [something](http://foo.com)')
    available_roles = models.CharField(default='', blank=True, max_length=255, help_text='List of comma-separated strings')
    # Will need to figure out how to migrate this over.
    photos = models.ManyToManyField(Photo, blank=True)
    image = models.ForeignKey(
        'vaquita.CustomImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    modified = models.DateTimeField(auto_now=True)
    show_commitment = models.BooleanField(blank=True, default=False, help_text='Whether to show the conditional commitment fields')
    max_participants = models.IntegerField(blank=True, default=0, help_text="Maximun number of people allowed to register")
    accessibility = models.TextField(default='', help_text="Indicate what the accessibility accomodations are for this location.")

    tags = TaggableManager(blank=True, help_text="Attendees will automatically be tagged with these tags")
    objects = ActionManager()

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('when'),
            FieldPanel('location'),
            FieldPanel('slug'),
        ]),
        FieldPanel('description'),
        ImageChooserPanel('image'),
        FieldPanel('tags'),
        FieldRowPanel([
            FieldPanel('public'),
            FieldPanel('max_participants'),
            FieldPanel('show_commitment'),
        ]),
        FieldPanel('accessibility'),
    ]

    @property
    def available_role_choices(self):
        for role in self.available_roles.split(','):
            role = role.strip()
            if role:
                yield role
    
    def is_full(self):
        return self.max_participants and self.attendee_set.count() >= self.max_participants

    def get_absolute_url(self):
        return reverse('extinctionr.actions:action', kwargs={'slug': self.slug})

    def signup(self, email, role, name='', notes='', promised=None, commit=0):
        if not isinstance(role, ActionRole):
            role = ActionRole.objects.get_or_create(name=role or '')[0]

        user = get_contact(email, name=name)
        atten, created = Attendee.objects.get_or_create(action=self, contact=user, role=role)
        if not created:
            if notes:
                atten.notes = notes
        else:
            atten.notes = notes
            atten.mutual_commitment = commit
        if promised:
            atten.promised = now()
        atten.save()
        return atten

    @property
    def html_title(self):
        return mark_safe(self.name.replace('\n','<br>').replace('\\n', '<br>'))

    @property
    def text_title(self):
        return self.name.replace('\\n', ' ')

    def __str__(self):
        return '%s on %s' % (self.name, self.when.strftime('%b %e, %Y @ %H:%M'))

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        for role in self.available_role_choices:
            ActionRole.objects.get_or_create(name=role)
        return ret

    @property
    def location_link(self):
        if self.location.startswith('['):
            link = markdown(self.location)
        else:
            link = '<a href="https://maps.google.com/?q={}">{}</a>'.format(quote(self.location), linebreaks(self.location))
        return mark_safe(link)
    
    @property
    def card_thumbnail_url(self):
        if self.photos:
            photo = self.photos.first()
            if photo:
                return photo.photo.url
        return None


class ActionRole(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)

    def __str__(self):
        return self.name


class Attendee(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    role = models.ForeignKey(ActionRole, on_delete=models.DO_NOTHING)
    promised = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(default='', blank=True)
    mutual_commitment = models.IntegerField(default=0, blank=True, db_column='mutual_committment')
    created = models.DateTimeField(auto_now_add=True, null=True)
    notified = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        unique_together = ('action', 'contact', 'role')

    def __str__(self):
        return '%s %s %s' % (self.action, self.contact, self.role)

    def get_absolute_url(self):
        return self.action.get_absolute_url() + '#attendees'


class ProposalManager(models.Manager):
    def propose(self, location, email, phone='', name=''):
        contact = get_contact(email, name=name, phone=phone)
        contact.tags.add('talk-request')
        prop = TalkProposal(requestor=contact)
        prop.location = location
        prop.save()
        return prop


class TalkProposal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    location = models.TextField()
    requestor = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    responded = models.DateTimeField(null=True, blank=True)
    responder = models.ForeignKey(USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    objects = ProposalManager()

    def __str__(self):
        return 'Talk at %s for %s' % (self.location[:20], self.requestor)

    def get_absolute_url(self):
        return '/talk'

    def get_talk_url(self):
        try:
            action = Action.objects.get(slug='xr-talk-%d' % self.id)
            return ''.join(['https://', get_current_site(None).domain, action.get_absolute_url()])
        except Action.DoesNotExist:
            return ''
