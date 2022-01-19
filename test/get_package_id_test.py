import os

import pytest

from certbotstratoapi import CertbotStratoApi


@pytest.mark.parametrize("test_input,expected", [
    ('domain-a.de', '7'),
    ('*.domain-a.de', '7'),
    ('test.domain-a.de', '7'),
    ('domain-b.de', '6'),
    ('*.domain-b.de', '6'),
    ('test.domain-b.de', '6'),
    ('domain-c.de', '5'),
    ('*.domain-c.de', '5'),
    ('test.domain-c.de', '5'),
    ('domain-d.de', '4'),
    ('*.domain-d.de', '4'),
    ('test.domain-d.de', '4'),
    ('domain-e.de', '2'),
    ('*.domain-e.de', '2'),
    ('test.domain-e.de', '2'),
    ('domain-f.de', '2'),
    ('*.domain-f.de', '2'),
    ('test.domain-f.de', '2'),
    ('domain-g.de', '1'),
    ('*.domain-g.de', '1'),
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
