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


@pytest.mark.parametrize('test_file,test_input,expected', [
    ('test/projectPage.html', 'test.domain-a.de', '7'),
    ('test/projectPage.html', 'test.domain-b.de', '6'),
    ('test/projectPage.html', 'test.domain-c.de', '5'),
    ('test/projectPage.html', 'test.domain-d.de', '4'),
    ('test/projectPage.html', 'test.domain-e.de', '2'),
    ('test/projectPage.html', 'test.domain-f.de', '2'),
    ('test/projectPage.html', 'test.domain-g.de', '1')
])
def test_get_package_id(test_file, test_input, expected, requests_mock):
    project_page = open(test_file, 'r').read()
    os.environ['CERTBOT_DOMAIN'] = test_input
    os.environ['CERTBOT_VALIDATION'] = 'xyz'
    strato = CertbotStratoApi()
    requests_mock.get(strato.api_url, text=project_page)

    strato.get_package_id()

    assert strato.package_id == expected
