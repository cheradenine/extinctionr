from datetime import datetime
import bleach
import jwt

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import TemplateDoesNotExist, get_template
from django.urls.exceptions import Resolver404
from django.utils.decorators import method_decorator
from django.utils.http import http_date
from django.views.decorators.cache import cache_page
from django.views.generic import FormView, DetailView, ListView, TemplateView

from extinctionr.circles.forms import IntakeForm
from extinctionr.circles.util import zipcode_lookup
from extinctionr.circles.models import VolunteerRequest
from extinctionr.utils import get_contact, get_last_contact, set_last_contact

from .models import PressRelease, Chapter


class RegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("email",)
        field_classes = {'email': forms.EmailField}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class ContactForm(forms.Form):
    message = forms.CharField()


class RegistrationView(FormView):
    form_class = RegistrationForm
    success_url = '/'
    template_name = 'registration/register.html'

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)


class ContactView(FormView):
    form_class = ContactForm
    success_url = '/contact'
    template_name = 'info/contact.html'

    def form_valid(self, form):
        from django.conf import settings
        from django.core.mail import send_mail
        from extinctionr.circles import get_circle
        outreach_circle = get_circle('outreach')
        address = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', 'unknown address'))
        subject = '[XR] Website Contact from {}'.format(address)
        message = form.cleaned_data['message']
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, outreach_circle.get_notification_addresses())
        messages.success(self.request, "Thanks for your feedback")
        return super().form_valid(form)


@method_decorator(cache_page(1200), name='dispatch')
class InfoView(TemplateView):
    def get(self, request, *args, **kwargs):
        page = kwargs['page']
        try:
            self.template_name = self.find_template(page)
        except TemplateDoesNotExist:
            raise Resolver404(page)
        tresp = super(InfoView, self).get(request, *args, **kwargs)
        response = HttpResponse(tresp.rendered_content)
        response['Vary'] = 'Cookie'
        if request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response

    @staticmethod
    def find_template(page):
        if page.endswith('.html'):
            page = page.split('.')[0]
        elif page.endswith('/'):
            page += 'index'
        try:
            template_name = 'pages/%s.html' % page
            template = get_template(template_name).template  # noqa F841
            return template_name
        except TemplateDoesNotExist:
            return None


# Wraps any Django URL Pattern and overrides the 'match' function.
class InfoViewUrlPattern():
    def __init__(self, pattern):
        self.pattern = pattern

    def match(self, path):
        match = self.pattern.match(path)
        if match:
            _, _, kwargs = match
            page = kwargs['page']
            if InfoView.find_template(page):
                return match
        return None

    # dynamically chain down to anything else to the wrapped pattern
    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.pattern, attr)


def wrap_info_path(path):
    path.pattern = InfoViewUrlPattern(path.pattern)
    return path


@method_decorator(cache_page(1200), name='dispatch')
class PRListView(ListView):
    def get_queryset(self):
        if self.request.user.has_perm('info.view_pressrelease'):
            return PressRelease.objects.all().order_by('-released')
        else:
            return PressRelease.objects.released()

    def render(self, *args, **kwargs):
        resp = super().render(*args, **kwargs)
        context = kwargs['context']
        resp['Last-Modified'] = http_date(context['object_list'].last().modified.timestamp())
        resp['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            resp['Cache-Control'] = 'private'
        return resp


@method_decorator(cache_page(1200), name='dispatch')
class PRDetailView(DetailView):
    def get_queryset(self):
        if self.request.user.has_perm('info.view_pressrelease'):
            return PressRelease.objects.all()
        else:
            return PressRelease.objects.released()

    def render(self, *args, **kwargs):
        resp = super().render(*args, **kwargs)
        context = kwargs['context']
        resp['Last-Modified'] = http_date(context['object'].modified.timestamp())
        resp['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            resp['Cache-Control'] = 'private'
        return resp


def list_chapters(request):
    chapters = serializers.serialize("json", Chapter.objects.all())
    context = {'chapters': chapters}
    return render(request, 'pages/groups/index.html', context)


class SignupFormView(FormView):
    template_name = 'pages/welcome/join.html'
    form_class = IntakeForm

    def decode_token(self, jwt_token):
        obj = jwt.decode(jwt_token.encode('UTF-8'), settings.SECRET_KEY, algorithms=['HS256'])
        served_at = datetime.fromisoformat(obj['served'])
        delta_seconds = (datetime.now() - served_at).seconds
        if delta_seconds < 5:
            raise ValueError

    def form_valid(self, form):
        data = form.cleaned_data
        jwt_token = data['message']
        try:
            self.decode_token(jwt_token)
        except:  # noqa E722
            return HttpResponseRedirect('/')

        postcode = data['zipcode']
        city, state = zipcode_lookup(postcode)
        person = get_contact(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            postcode=postcode,
            city=city,
            state=state,
            phone=data['phone'])

        # TODO: should we record this?
        ip_address = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', 'unknown address'))

        if data["volunteer"]:
            person.tags.add('volunteer')
            skills = data['skills']

            message = bleach.clean(data['anything_else'])
            if data["skill_other"]:
                other_skill = bleach.clean(data["skill_other_value"])
                # was going to make this another skill tag but don't want random users
                # adding tags
                message = 'otherskill: {0}\nmessage: {1}'.format(other_skill, message)

            try:
                volunteer = VolunteerRequest.objects.get(contact__email=person.email)
            except VolunteerRequest.DoesNotExist:
                volunteer = VolunteerRequest.objects.create(contact=person, message=message)
            for skill in skills:
                volunteer.tags.add(skill)

        set_last_contact(self.request, person)
        return HttpResponseRedirect('/welcome/thankyou')

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        initial = super().get_initial()
        now = datetime.now().isoformat()
        token = jwt.encode({'served': now}, settings.SECRET_KEY, algorithm='HS256')
        # todo: would be cool to move this into the field at runtime
        # to further thwart the bots.
        initial['message'] = token.decode('UTF-8')
        initial['email'] = self.request.GET.get('email', None)
        return initial


def serve_thankyou(request):
    # If there is a contact info in the session, then they entered it.
    # Otherwise go back to join page.
    if not request.session.get('last-contact', None):
        return HttpResponseRedirect('/join')
    return render(request, 'pages/welcome/thankyou.html', {})
