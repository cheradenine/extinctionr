import requests
import uuid
import logging

from django.conf import settings

AN_ENTRY_POINT = "https://actionnetwork.org/api/v2/"
AN_HEADERS = {
    'OSDI-API-Token' : settings.AN_API_KEY,
    'Content-Type' : 'application/json',
}

logger = logging.getLogger('circles.anapi')

def _get_people_api():
    if AN_HEADERS['OSDI-API=Token'] == 'Debug':
        return None

    resp = requests.get(AN_ENTRY_POINT, headers=AN_HEADERS)
    if resp.status_code != 200:
        logger.warning(
            'get_people_api failed with {0}:{1}'.format(resp.status_code, resp.text)
        )

    try:
        people_api = resp.json()['_links']["osdi:person_signup_helper"]["href"]
    except KeyError:
        logger.warning(
            'get_people_api failed to parse response: {0}'.format(resp.text)
        )

    # TODO: maybe cache this.
    return people_api


def add_to_action_networks(contact):
    people_url = _get_people_api()
    if not people_url:
        return

    id = uuid.uuid3(uuid.NAMESPACE_DNS, 'xrboston.org')
    payload = {
        "person": {
            "identifiers": [ id.hex ],
            "family_name" : contact.last_name,
            "given_name" : contact.first_name,
            "postal_address": [ { "postal_code": contact.address.postcode}],
            "email_addresses" : [ { "address" : contact.email }],
            "custom_fields" : [
                { "phone" : contact.phone.as_national },
            ],
        }
    }
    resp = requests.post(people_url, headers=AN_HEADERS, json=payload)
    if resp.status_code != 200:
        logger.warning('add_person failed: {0}'.format(resp.text))
