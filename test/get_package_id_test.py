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
