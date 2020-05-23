from contacts.models import Contact, Address
from django.conf import settings
from django.contrib.sites.models import Site

def _get_names(name):
    sname = name.split(' ', 1)
    if len(sname) == 2:
        first_name, last_name = sname
    else:
        first_name = sname[0]
        last_name = '?'
    return (first_name, last_name)


def _update_address(user, address):
    updated = False
    for k, v in address.items():
        if v and getattr(user.address, k, None) is None:
            setattr(user.address, k, v)
            updated = True
    if updated:
        user.address.save()


def get_contact(email, name='', first_name='', last_name='', **kwargs):
    email = email.lower().strip()
    assert email
    addr_keys = [f.name for f in Address._meta.fields]
    addr_keys.remove('id')
    address = {}
    for k in addr_keys:
        if k in kwargs:
            address[k] = kwargs.pop(k)

    try:
        user = Contact.objects.get(email=email)
    except Contact.DoesNotExist:
        if not (first_name and last_name):
            first_name, last_name = _get_names(name)
        user = Contact.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            address=Address.objects.create(**address) if address else None,
            **kwargs
        )
    resave = False
    for k, v in kwargs.items():
        if v and getattr(user, k, None) is None:
            setattr(user, k, v)
            resave = True
    if last_name and user.last_name in ('', '?', 'unknown'):
        user.last_name = last_name
        resave = True
    if first_name and user.first_name in ('', '?', 'unknown'):
        user.first_name = first_name
        resave = True

    if address:
        if not user.address:
            user.address = Address.objects.create(**address)
            resave = True
        else:
            _update_address(user, address)

    if resave:
        user.save()
    return user


def get_last_contact(request):
    last = request.session.get('last-contact', None)
    if last:
        return Contact.objects.get(pk=last)


def set_last_contact(request, contact):
    if contact:
        request.session['last-contact'] = contact.id
    else:
        request.session.pop('last-contact', None)

def base_url():
    current_site = Site.objects.get_current()
    scheme = 'http' if settings.DEBUG else 'https'
    return '%s://%s' % (scheme, current_site.domain)
