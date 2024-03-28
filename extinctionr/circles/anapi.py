import requests
import uuid
import logging
from http.client import HTTPConnection
from contextlib import contextmanager

from django.conf import settings


logger = logging.getLogger("circles.anapi")


@contextmanager
def verbose_http_logging(payload):
    http_debug_level = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 1

    root_logger = logging.getLogger()
    root_log_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)

    requests_logger = logging.getLogger("urllib3")
    requests_log_level = requests_logger.level
    requests_log_propagate = requests_logger.propagate
    requests_logger.setLevel(logging.DEBUG)
    requests_logger.propagate = True
    try:
        root_logger.info(payload)
        yield
    finally:
        requests_logger.propagate = requests_log_propagate
        requests_logger.setLevel(requests_log_level)
        root_logger.setLevel(root_log_level)
        HTTPConnection.debuglevel = http_debug_level


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

    if contact.phone and contact.phone.as_national:
        person["phone_number"] = [{"number" : str(contact.phone.national_number)}]

    payload = {
        "person": person,
        "triggers": {"autoresponse": {"enabled": True}},
    }

    with verbose_http_logging(payload):
        resp = requests.post(signup_url, headers=headers, json=payload, timeout=10.0)
        if resp.status_code != 200:
            logger.error("POST to %s failed: %s", signup_url, resp.text)
