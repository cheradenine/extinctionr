import requests
import uuid
import logging

from django.conf import settings


logger = logging.getLogger("circles.anapi")


def add_to_action_networks(contact):
    headers = {
        "OSDI-API-Token": settings.AN_API_KEY,
        "Content-Type": "application/json",
    }

    signup_form_id = settings.AN_SIGNUP_FORM_ID

    if not signup_form_id:
        return

    signup_url = f"https://actionnetwork.org/api/v2/forms/{signup_form_id}/submissions"

    id = uuid.uuid3(uuid.NAMESPACE_DNS, "xrboston.org")

    person = {
        "identifiers": [id.hex],
        "family_name": contact.last_name,
        "given_name": contact.first_name,
        "email_addresses": [{"address": contact.email}],
    }

    if contact.address:
        person["postal_addresses"] = [{"postal_code": contact.address.postcode}]

    if contact.phone:
        person["phone_numbers"] = [contact.phone.as_national]

    payload = {
        "person": person,
        "triggers": {"autoresponse": {"enabled": True}},
    }
    resp = requests.post(signup_url, headers=headers, json=payload, timeout=10.0)

    if resp.status_code != 200:
        logger.error("POST to %s failed: %s", signup_url, resp.text)
