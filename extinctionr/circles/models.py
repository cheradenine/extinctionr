from collections import defaultdict
import json

from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.functional import cached_property
from markdownx.models import MarkdownxField
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from contacts.models import Contact
from extinctionr.utils import get_contact

ROLE_CHOICES = {
    'int': 'Internal Coordinator',
    'ext': 'External Coordinator',
    'member': 'Member'
}

LEAD_ROLES = ('int', 'ext', 'lead')


class Circle(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, db_index=True)
    purpose = MarkdownxField(default='', help_text='Describe the mandates for this group')
    sensitive_info = MarkdownxField(default='', blank=True, help_text='Information for members only')
    members = models.ManyToManyField(to=Contact, through='CircleMember', blank=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    color = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(max_length=255, blank=True, null=True, help_text='Public email address for this group')
    available_roles = models.CharField(max_length=255, blank=True, default='int,ext,member', help_text='Comma-separated names of roles')
    role_description = MarkdownxField(default='', blank=True, help_text='Describe additional roles (markdown format')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        parents = list(p.name for p in self.parents)
        parents.reverse()
        parents.append(self.name)
        return ' :: '.join(parents)

    def clean(self):
        super().clean()
        available = [a.strip() for a in self.available_roles.split(',') if a.strip()]
        # for role in ROLE_CHOICES.keys():
        #     if role not in available:
        #         available.append(role)
        self.available_roles = ','.join(available)

    def get_role_choices(self):
        choices = []
        for role in self.available_roles.split(','):
            choice = ROLE_CHOICES.get(role, role.capitalize())
            choices.append((role, choice))
        return choices

    @property
    def wiki_home(self):
        return self.name.lower().replace(' ', '-').replace('&', '-')

    @cached_property
    def recursive_members(self):
        members = defaultdict(set)
        for mem in CircleMember.objects.filter(circle=self).select_related('contact').order_by('role', 'pk'):
            members[mem.contact].add((mem.role, mem.verbose_role, mem.id, mem.circle_id))
        for circle in self.children:
            for contact, roles in circle.recursive_members.items():
                members[contact].update(roles)
        return members

    @cached_property
    def recursive_members_count(self):
        return len(self.recursive_members)

    @cached_property
    def children(self):
        return list(self.circle_set.all().prefetch_related('members'))

    @cached_property
    def member_list(self):
        return list(CircleMember.objects.filter(circle=self).select_related('contact').order_by('role', 'pk'))

    @cached_property
    def lead_list(self):
        return list(self.leads.all())

    @cached_property
    def leads(self):
        return Contact.objects.filter(circlemember__role__in=LEAD_ROLES, circlemember__circle=self)

    @cached_property
    def coordinators(self):
        return CircleMember.objects.filter(circle=self, role__in=LEAD_ROLES).order_by('role', 'pk')

    @property
    def external_coordinators(self):
        return self.coordinators.filter(role='ext')

    @property
    def internal_coordinators(self):
        return self.coordinators.filter(role__in=('int', 'lead'))

    def get_absolute_url(self):
        return reverse('circles:detail', kwargs={'pk': self.id})

    def get_path(self):
        parents = list(p.name for p in self.parents)
        parents.reverse()
        parents.append(self.name)
        path = '/'.join(parents)
        path += '/index.yaml'
        return path.encode('utf8')

    @property
    def parents(self):
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent

    @property
    def bgcolor(self):
        return self.color or (self.parent.bgcolor if self.parent else '')

    @property
    def has_children(self):
        return self.circle_set.exists()
    
    @cached_property
    def public_email(self):
        email = self.email
        if not email:
            email = self.parent.public_email if self.parent else ''
        return email

    def get_notification_addresses(self):
        addresses = set()
        public_address = self.public_email
        if public_address:
            addresses.add(public_address)
        for lead in self.lead_list:
            addresses.add(lead.email)
        return addresses

    def get_member_emails(self):
        emails = set((m.email for m in self.recursive_members))
        return ','.join(emails)

    def add_member(self, email, name, contact=None, role='member'):
        contact = contact or get_contact(email, name=name)
        CircleMember.objects.get_or_create(circle=self, contact=contact, role=role)

    def remove_member(self, contact, role='member', who=None):
        """
        Removes the member and/or any requests for membership
        """
        CircleMember.objects.filter(circle=self, contact=contact, role=role).delete()
        MembershipRequest.objects.filter(circle=self, requestor=contact).update(confirmed_by=who)

    def request_membership(self, email='', name='', contact=None):
        contact = contact or get_contact(email, name=name)
        if not self.members.filter(pk=contact.id).exists():
            try:
                MembershipRequest.objects.get_or_create(circle=self, requestor=contact)
            except MultipleObjectsReturned:
                pass
            return contact
        else:
            return False

    def approve_membership(self, contact, who):
        for req in MembershipRequest.objects.filter(circle=self, requestor=contact):
            req.confirmed_by = who
            req.save()

    def can_manage(self, user):
        return user.has_perm('circles.change_circle') or self.leads.filter(pk=get_contact(email=user.email).id).exists()

    def is_member(self, user):
        email = user.email
        for member in self.recursive_members:
            if member.email == email:
                return True
        return False

    def is_pending(self, request):
        if request.user.is_authenticated:
            contact = get_contact(request.user.email)
        else:
            contact = None
        if contact:
            try:
                return MembershipRequest.objects.get(circle=self, requestor=contact).confirm_date is None
            except MembershipRequest.DoesNotExist:
                return False
        else:
            return str(self.id) in request.session.get('circle_requests', {})
        return False



class CircleMember(models.Model):
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    role = models.CharField(max_length=255)
    join_date = models.DateTimeField(auto_now_add=True)

    @property
    def verbose_role(self):
        return ROLE_CHOICES.get(self.role, self.role.capitalize())

    class Meta:
        unique_together = ('circle', 'contact', 'role')

    def __str__(self):
        return '{} {}'.format(self.circle, self.contact)

    def get_absolute_url(self):
        return self.circle.get_absolute_url()



class MembershipRequest(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE)
    requestor = models.ForeignKey(Contact, on_delete=models.CASCADE)
    confirmed_by = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name='confirmation_set')
    confirm_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s -> %s' % (self.requestor, self.circle)

    def get_absolute_url(self):
        return self.circle.get_absolute_url()

    def save(self, *args, **kwargs):
        if self.confirmed_by and not self.confirm_date:
            self.confirm_date = now()
        super().save(*args, **kwargs)
        if self.confirmed_by:
            self.circle.add_member(self.requestor.email, str(self.requestor), contact=self.requestor, role='member')
        else:
            self.circle.remove_member(self.requestor, role='member')


class CircleJob(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE)
    creator = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL)
    job = MarkdownxField(default='')
    filled = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name="my_job_set", help_text="Who will fill this job?")
    filled_on = models.DateTimeField(null=True, blank=True)
    asap = models.BooleanField(blank=True, default=False, help_text="This job needs to be filled as soon as possible")
    title = models.CharField(max_length=255, blank=True, default='')

    def get_absolute_url(self):
        return '{}jobs/{}'.format(self.circle.get_absolute_url(), self.id)

    def __str__(self):
        return 'Job for {}'.format(self.circle)


class Couch(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    modified = models.DateTimeField(db_index=True, auto_now=True)
    owner = models.ForeignKey(Contact, on_delete=models.CASCADE)
    availability = MarkdownxField(default='', help_text="Enter dates/times this room is available")
    info = MarkdownxField(default='')
    public = models.BooleanField(default=False, db_index=True, help_text="Show publicly")

    class Meta:
        verbose_name_plural = 'couches'

    def __str__(self):
        return str(self.owner)

    def get_absolute_url(self):
        return reverse('circles:person', kwargs={'contact_id': self.owner_id}) + '#couches'

    def is_me(self, user):
        return get_contact(user.email) == self.owner


class Signup(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.CharField(max_length=255, blank=True, default='')
    raw_data = models.TextField(blank=True, default='{}')

    json_fields = ('email', 'first_name', 'last_name', 'phone', 'zipcode', 'interests', 'other_groups', 'committment', 'working_group', 'anything_else')

    @property
    def data(self):
        return json.loads(self.raw_data)

    @data.setter
    def data(self, obj):
        self.raw_data = json.dumps(obj)


    for key in json_fields:
        exec ('def {0}(self):\n    return self.data.get("{0}", None)'.format(key))


class TaggedVolunteerRequest(TaggedItemBase):
    content_object = models.ForeignKey('VolunteerRequest', on_delete=models.CASCADE)


class VolunteerRequest(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL)
    tags = TaggableManager(through=TaggedVolunteerRequest)
    message = models.TextField(blank=True, default='')

