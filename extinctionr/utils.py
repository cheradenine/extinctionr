from contacts.models import Contact, Address
from django.conf import settings
from django.contrib.sites.models import Site


def _get_names(name, first, last):
    sname = name.split(' ', 1)
    if len(sname) == 2:
        first_name, last_name = sname
    else:
        first_name = sname[0]
        last_name = '?'
    first_name = first if first else first_name
    last_name = last if last else last_name
    return (first_name, last_name)


def _update_model_attr(model, k, v):
    # Updates model field if needed.
    if v and getattr(model, k, None) != v:
        setattr(model, k, v)
        return True
    return False


def _update_model(model, **kwargs):
    updated = False
    for k, v in kwargs.items():
        updated = _update_model_attr(model, k, v) or updated
    return updated


def _has_name(name):
    return name not in ('', '?', 'unknown')
            

def get_contact(email, name='', first_name='', last_name='', **kwargs):
    email = email.lower().strip()
    assert email
    addr_keys = [f.name for f in Address._meta.fields]
    addr_keys.remove('id')

    # Create address dict from fields in kwargs.
    address = {k : kwargs.pop(k) for k in addr_keys if k in kwargs}

    is_update = False
    try:
        user = Contact.objects.get(email=email)
        is_update = True
    except Contact.DoesNotExist:
        if not (first_name and last_name):
            first_name, last_name = _get_names(name, first_name, last_name)
        user = Contact.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            address=Address.objects.create(**address) if address else None,
            **kwargs
        )

    resave = _update_model(user, **kwargs)

    # Maybe update new name info.
    if _has_name(last_name):
        resave = _update_model_attr(user, 'last_name', last_name)
    if _has_name(first_name):
        resave = _update_model_attr(user, 'first_name', first_name)

    if address:
        # User had no address.
        if not user.address:
            user.address = Address.objects.create(**address)
            resave = True
        elif is_update:
            if _update_model(user.address, **address):
                user.address.save()

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
