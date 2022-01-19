import os

import pytest

from certbotstratoapi import CertbotStratoApi


@pytest.mark.parametrize("test_input,expected", [
    ('domain-a.de', 'domain-a.de'),
    ('*.domain-a.de', 'domain-a.de'),
    ('test.domain-a.de', 'domain-a.de')
])
def test_parse_second_level_domain(test_input, expected):
    os.environ['CERTBOT_DOMAIN'] = test_input
    os.environ['CERTBOT_VALIDATION'] = 'xyz'

    strato = CertbotStratoApi()

    assert strato.second_level_domain_name == expected


@pytest.mark.parametrize("test_input,expected", [
    ('test.domain-a.de', '7'),
    ('test.domain-b.de', '6'),
    ('test.domain-c.de', '5'),
    ('test.domain-d.de', '4'),
    ('test.domain-e.de', '2'),
    ('test.domain-f.de', '2'),
    ('test.domain-g.de', '1')
])
def test_get_package_id(test_input, expected, requests_mock):
    project_page = open('test/projectPage.html', 'r').read()
    os.environ['CERTBOT_DOMAIN'] = test_input
    os.environ['CERTBOT_VALIDATION'] = 'xyz'
    strato = CertbotStratoApi()
    requests_mock.get(strato.api_url, text=project_page)

    strato.get_package_id()

    assert strato.package_id == expected
