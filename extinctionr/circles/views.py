from io import TextIOWrapper
import csv

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic.edit import FormView
from django.utils.timezone import now
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseRedirect
from django import forms
from django.views import generic

from extinctionr.utils import get_contact, get_last_contact, set_last_contact
from .models import Circle, Contact, CircleJob, Couch, LEAD_ROLES, Signup, VolunteerRequest
from . import get_circle
from .forms import (
    FindPeopleForm, MembershipRequestForm, ContactForm, 
    CouchForm, ContactAutocomplete, IntakeForm,
    VOLUNTEER_SKILL_CHOICES)


@login_required
def add_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    form = ContactForm(circle, request.POST)
    if form.is_valid() and circle.can_manage(request.user):
        data = form.cleaned_data
        email = data['email'].lower()
        name = data['name']
        contact = data['contact']
        role = data['role']
        circle.add_member(email, name, contact=contact, role=role)
    return redirect(circle.get_absolute_url())


@login_required
def del_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    contact = get_object_or_404(Contact, pk=request.POST['id'])
    me = get_contact(email=request.user.email)
    if me == contact or circle.can_manage(request.user):
        role = request.POST.get('role', 'member')
        circle.remove_member(contact, role=role, who=request.user)
    return redirect(circle.get_absolute_url())

@login_required
def approve_membership(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    contact = get_object_or_404(Contact, pk=request.POST['id'])
    if circle.can_manage(request.user):
        circle.approve_membership(contact, who=get_contact(email=request.user.email))
        messages.success(request, "Approved {}!".format(contact))

    return redirect(circle.get_absolute_url())


def request_membership(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    if request.method == 'POST':
        form = MembershipRequestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            contact = circle.request_membership(data['email'], data['name'])
            if contact and not request.user.is_authenticated:
                set_last_contact(request, contact)
                circle_requests = request.session.get('circle_requests', {})
                circle_requests[str(circle.id)] = True
                request.session['circle_requests'] = circle_requests
            messages.success(request, "Thank you for signing up for {}!".format(circle))
    return redirect(circle.get_absolute_url())


def find_field(fields, search_for):
    for field in fields:
        if field.lower().startswith(search_for):
            return field
    raise ValueError(search_for)


@login_required
def csv_import(request):
    ctx = {}
    can_import = request.user.has_perm('circles.change_circle')
    ctx['can_import'] = can_import
    if can_import and request.method == 'POST':
        f = TextIOWrapper(request.FILES['csv'].file, encoding=request.encoding)
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        email_field = find_field(fields, 'email')
        first_name_field = find_field(fields, ('first', 'first name', 'fname'))
        last_name_field = find_field(fields, ('last', 'last name', 'lname'))
        try:
            wg_field = find_field(fields, ('circle', 'working group', 'wg'))
        except ValueError:
            wg_field = None

        try:
            phone_field = find_field(fields, ('phone number', 'phone'))
        except ValueError:
            phone_field = None

        try:
            tag_field = find_field(fields, ('tags', 'tag'))
        except ValueError:
            tag_field = None

        contacts = set()
        memberships = []
        for row in reader:
            contact = get_contact(row[email_field],
                first_name=row[first_name_field],
                last_name=row[last_name_field],
                phone=row[phone_field] if phone_field else None)
            contacts.add(contact)
            messages.success(request, 'Found {}'.format(contact))
            if wg_field and row[wg_field]:
                wg = row[wg_field].split('-')[0].strip()
                try:
                    circle = Circle.objects.filter(name__iexact=wg).order_by('-pk')[0]
                except IndexError:
                    messages.error(request, 'Could not find circle named {}'.format(wg))
                else:
                    if circle.request_membership(contact=contact):
                        messages.success(request, 'Requested membership for {} to {}'.format(contact, circle))
            if tag_field and row[tag_field]:
                contact.tags.add(*[t.strip() for t in row[tag_field].split(',')])
        return redirect('circles:person-import')
    response = render(request, 'circles/csv.html', ctx)
    response['Cache-Control'] = 'private'
    return response


@method_decorator(cache_page(1200), name='dispatch')
class BaseCircleView(generic.View):
    def render(self, request, template_name, **response_kwargs):
        response = super().render(request, template_name, **response_kwargs)
        response['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response


@method_decorator(login_required, name='dispatch')
class PersonView(BaseCircleView, FormView):
    template_name = 'circles/person.html'
    form_class = CouchForm

    def form_valid(self, form):
        info = form.cleaned_data['info']
        availability = form.cleaned_data['availability']
        public = form.cleaned_data['public']
        me = get_contact(email=self.request.user.email)
        me.couch_set.create(info=info, availability=availability, public=public)
        messages.success(self.request, "Thank you for your generosity!")
        return HttpResponseRedirect('/circle/person/me/')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        me = get_contact(email=self.request.user.email)
        contact_id = self.kwargs.get('contact_id', None)
        if contact_id is None:
            contact = me
        else:
            contact = get_object_or_404(Contact, pk=contact_id)

        ctx = {
            'contact': contact,
            'leads': Circle.objects.filter(circlemember__contact=contact, circlemember__role__in=LEAD_ROLES).distinct(),
            'members': Circle.objects.filter(circlemember__contact=contact).exclude(circlemember__role__in=LEAD_ROLES),
            'is_me': contact == me,
            }
        couches = contact.couch_set.all()
        if not ctx['is_me']:
            couches = couches.filter(public=True)
        else:
            ctx['form'] = self.form_class()
        ctx['couches'] = couches
        return ctx


class SignupView(BaseCircleView, FormView):
    template_name = 'pages/welcome/signup.html'
    form_class = IntakeForm

    def form_valid(self, form):
        data = form.cleaned_data
        person = get_contact(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            postcode=data['zipcode'],
            phone=data['phone'])
        person.tags.add('self-signup')

        working_group = data['working_group']
        ip_address = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', 'unknown address'))

        signup_obj = Signup(
                ip_address=ip_address,
                contact=person
        )
        signup_obj.data = data
        if working_group != 'UNKNOWN':
            circle = get_circle(data['working_group'])
            if circle and circle.request_membership(contact=person):
                messages.success(self.request, 'Requested membership in {}'.format(circle))
        signup_obj.save()
        set_last_contact(self.request, person)
        return HttpResponseRedirect('/welcome/guide')

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        initial = super(SignupView, self).get_initial()

        initial['working_group'] = 'UNKNOWN'
        initial['committment'] = 'full'

        return initial




class CouchListView(BaseCircleView, generic.ListView):
    template_name = 'circles/couches.html'

    def get_queryset(self):
        qset = Couch.objects.all().order_by('-modified')
        if not self.request.user.has_perm('circles.view_couch'):
            qset = qset.filter(public=True)
        return qset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.has_perm('circles.change_couch')
        return context


class CircleView(BaseCircleView, generic.DetailView):
    template_name = 'circles/circle.html'
    def get_queryset(self):
        return Circle.objects.select_related('parent').prefetch_related('members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        circle = context['object']
        if self.request.user.is_authenticated:
            is_lead = circle.can_manage(self.request.user)
            # only members of the group can see the contact info of the coordinators
            context['is_member'] = context['can_see_leads'] = circle.is_member(self.request.user)
            context['can_see_members'] = is_lead or self.request.user.has_perm('circles.view_circle')
            # context['can_see_leads'] = self.request.user.is_authenticated
            context['is_lead'] = is_lead
            context['members'] = sorted(circle.recursive_members.items(), key=lambda m: (m[0].last_name.lower(), m[0].first_name.lower()))
            context['pending'] = circle.membershiprequest_set.filter(confirmed_by=None)
            context['form'] = ContactForm(circle, initial={'role': 'member'})
            context['jobs'] = CircleJob.objects.filter(circle=circle)
            context['can_edit_member'] = self.request.user.has_perm('circles.circlemember_change')
            # if they're logged in, this is not relevant
            if 'circle_requests' in self.request.session:
                del self.request.session['circle_requests']
        if not context.get('is_lead', None):
            initial = {'circle_id': circle.id}
            last_contact = get_last_contact(self.request)
            if last_contact:
                initial['email'] = last_contact.email
                initial['name'] = str(last_contact)
            if not context.get('is_member'):
                context['request_form'] = MembershipRequestForm(initial=initial)
        if not (context.get('is_lead', None) or context.get('is_member', None)):
            context['is_pending'] = circle.is_pending(self.request)
        return context


class TopLevelView(BaseCircleView, generic.ListView):
    template_name = 'circles/outer.html'

    def get_queryset(self):
        return Circle.objects.filter(parent__isnull=True).prefetch_related('members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_see_members'] = self.request.user.has_perm('circles.view_circle')
        context['can_see_leads'] = self.request.user.is_authenticated
        return context


class JobView(BaseCircleView, generic.TemplateView):
    template_name = 'circles/jobs.html'

    def post(self, request, *args, **kwargs):
        job = get_object_or_404(CircleJob, pk=request.POST['id'])
        who = get_contact(email=self.request.user.email)
        job.filled = who
        job.filled_on = now()
        job.save()
        role = job.title or 'member'
        job.circle.add_member(who.email, str(who), contact=who, role=role)
        messages.success(request, "Thanks for signing up for this job!")
        return HttpResponse('ok')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qset = CircleJob.objects.select_related('circle').order_by('-asap', 'id')
        circle_id = self.kwargs.get('pk', None)
        if circle_id:
            context['circle'] = get_object_or_404(Circle, pk=circle_id)
            qset = qset.filter(circle__id=circle_id)
        else:
            qset = qset.filter(filled__isnull=True)
        job_id = self.kwargs.get('job_id', None)
        if job_id:
            qset = qset.filter(pk=job_id)
            context['job_id'] = job_id
        context['can_change'] = can_change = self.request.user.has_perm('circles.change_circlejob')
        context['jobs'] = qset
        return context


@method_decorator(login_required, name='dispatch')
class FindFormView(FormView):
    template_name = 'circles/find.html'
    form_class = FindPeopleForm

    def form_valid(self, form):
        tags = form.cleaned_data['tags']
        actions = form.cleaned_data['actions']
        contacts = Contact.objects
        if tags:
            contacts = contacts.filter(tags__in=tags)
        if actions:
            contacts = contacts.filter(attendee__action__in=actions)

        if not (actions or tags):
            contacts = []
        else:
            contacts = contacts.distinct()
        ctx = {
            'form': FindPeopleForm(initial=form.cleaned_data),
            'tags': tags,
            'actions': actions,
            'contacts': contacts,
        }
        response = render(self.request, self.template_name, ctx)
        response['Cache-Control'] = 'private'
        return response


@login_required
def csv_export(request):
    if request.user.has_perm('contacts.view_contact'):
        contact_ids = [c for c in request.GET.get('contacts', '').split(',') if c]
        contacts = Contact.objects.filter(id__in=contact_ids)
    else:
        contacts = []
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="contacts.csv"'
    csv_writer = csv.writer(resp)
    header = ('Email', 'First Name', 'Last Name', 'Phone', 'City', 'Tags')
    csv_writer.writerow(header)
    for contact in contacts:
        csv_writer.writerow((
            contact.email,
            contact.first_name,
            contact.last_name,
            contact.phone,
            contact.address.city if contact.address else None,
            ','.join(contact.tags.names())))
    return resp


@login_required
def signup_export(request):
    if request.user.has_perm('circles.view_signup'):
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="signups.csv"'
        csv_writer = csv.writer(resp)
        header = ['Date', 'IP Address', 'Contact ID']
        wrote_header = False
        for signup in Signup.objects.all():
            data = signup.data
            row = [signup.created, signup.ip_address, signup.contact_id]
            if not wrote_header:
                header.extend(sorted(data))
                csv_writer.writerow(header)
                wrote_header = True
            for key, value in sorted(data.items()):
                row.append(value)
            csv_writer.writerow(row)
        return resp


@login_required
def volunteer_export(request):
    if request.user.has_perm('contacts.view_contact'):
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="volunteers.csv"'
        csv_writer = csv.writer(resp)
        header = [
            'Created', 'Email', 'First Name', 'Last Name', 
            'Phone', 'City', 'State', 'Zipcode', 
            'Message'
        ]
        skill_tags = VOLUNTEER_SKILL_CHOICES
        skill_header = [skill[1] for skill in VOLUNTEER_SKILL_CHOICES]
        header = header + skill_header
        csv_writer.writerow(header)
        volunteers = VolunteerRequest.objects.all()
        for volunteer in VolunteerRequest.objects.all():
            contact = volunteer.contact
            address = contact.address
            # art, social, foo
            # 'True', 'False', 'True', etc.
            skills = set(volunteer.tags.names())
            skill_data = [str(skill[0] in skills) for skill in skill_tags]

            csv_writer.writerow((
                volunteer.created.isoformat(),
                contact.email,
                contact.first_name,
                contact.last_name,
                contact.phone,
                address.city if address else None,
                address.state if address else None,
                address.postcode if address else None,
                volunteer.message,
                *skill_data))
        return resp
