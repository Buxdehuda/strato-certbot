import os

import pytest

from certbotstratoapi import CertbotStratoApi


@pytest.fixture(autouse=True)
def setup_env_vars():
    os.environ['CERTBOT_DOMAIN'] = 'example.com'
    os.environ['CERTBOT_VALIDATION'] = 'xyz'


def test_records_are_empty_at_begin():
    strato = CertbotStratoApi()

    assert len(strato.records) == 0


def test_add_record():
    strato = CertbotStratoApi()

    strato.add_txt_record('subdomain', 'TXT', 'myvalue')

    assert len(strato.records) == 1
    assert strato.records[0]['prefix'] == 'subdomain'
    assert strato.records[0]['type'] == 'TXT'
    assert strato.records[0]['value'] == 'myvalue'


def test_set_acme_record():
    strato = CertbotStratoApi()

    strato.set_amce_record()

    assert len(strato.records) == 1
    assert strato.records[0]['prefix'] == '_acme-challenge'
    assert strato.records[0]['type'] == 'TXT'
    assert strato.records[0]['value'] == 'xyz'


def test_remove_record():
    strato = CertbotStratoApi()

    strato.add_txt_record('subdomain', 'TXT', 'myvalue')
    strato.remove_txt_record('subdomain', 'TXT')

    assert len(strato.records) == 0


def test_reset_acme_record():
    strato = CertbotStratoApi()

    strato.set_amce_record()
    strato.reset_amce_record()

    assert len(strato.records) == 0


def test_get_records():
    # TODO: If someone can send me the html source for the list
    # we can test this method
    assert True
