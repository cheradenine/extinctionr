from django import forms
from dal import autocomplete
from taggit.models import Tag
from extinctionr.actions.models import Action
from .models import Contact

class ContactForm(forms.Form):
    contact = forms.ModelChoiceField(
        required=False,
        queryset=Contact.objects.all(),
        label='Lookup',
        widget=autocomplete.ModelSelect2(url='circles:person-autocomplete', attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(required=False, label="Name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    role = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'form-control text-center custom-select custom-select-lg', 'placeholder': 'Role'}))

    def __init__(self, circle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = circle.get_role_choices()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['contact']:
            if cleaned_data['role'] == 'lead':
                raise forms.ValidationError('contact required')
            if not (cleaned_data['email'] and cleaned_data['name']):
                raise forms.ValidationError('email or contact required')
        return cleaned_data


class MembershipRequestForm(forms.Form):
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(required=True, label="Name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    circle_id = forms.IntegerField(required=True, widget=forms.HiddenInput())


class FindPeopleForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Tag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'class': 'form-control', 'placeholder': 'Tags'})
    )
    actions = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Action.objects.filter(attendee__isnull=False).distinct().order_by('-when'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )


class CouchForm(forms.Form):
    availability = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Dates/times the room or couch is available'}))
    info = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Other info'}))
    public = forms.BooleanField(required=False, label="Show my contact on the public page")


VOLUNTEER_SKILL_CHOICES = [
    ("action", "Action"),
    ("art", "Art"),
    ("music", "Music"),
	("video", "Video"),
    ("finance", "Fundraising"),
    ("social", "Social Media"),
    ("comms", "Communications"),
    ("strategy", "Strategy"),
    ("tech", "Tech"),
    ("outreach", "Outreach"),
    ("events", "Events"),
    ("education", "Education"),
    ("regen", "Regenerative Culture"),
]

class IntakeForm(forms.Form):
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'})
    )
    email = forms.EmailField(
        label="Email", 
        required=True, widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'})
    )
    zipcode = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    volunteer = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'data-toggle': 'collapse', 'data-target' : '#volunteer_form'})
    )
    skills = forms.MultipleChoiceField(
        required=False,
        choices=VOLUNTEER_SKILL_CHOICES, 
        widget=forms.CheckboxSelectMultiple()
    )
    skill_other = forms.BooleanField(
        required=False
    )
    skill_other_value = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Other'})
    )
    anything_else = forms.CharField(
        required=False, 
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '(Optional) anything else you want us to know?'})
    )
    message = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    def clean_zipcode(self):
        zipcode = self.cleaned_data['zipcode']
        if not (zipcode.isdigit() and len(zipcode) == 5):
            raise forms.ValidationError('Invalid zipcode')
        return zipcode


class ContactAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()

        qs = Contact.objects.all()

        if self.q:
            qs = qs.filter(email__istartswith=self.q) | qs.filter(first_name__istartswith=self.q)

        return qs

