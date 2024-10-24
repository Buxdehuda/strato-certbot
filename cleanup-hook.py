#!/usr/bin/env python3
"""Cleanup hook in Certbot to Strato dns"""
import json
import os
import sys

from certbotstratoapi import CertbotStratoApi


def main():
    """Run cleanup hook."""
    # get authentication data
    with open(
            os.path.dirname(__file__) + os.path.normcase('/'+sys.argv[1]),
            encoding='UTF-8',
            ) as file:
        auth = json.load(file)
        username = auth.get('username')
        password = auth.get('password')
        totp_secret = auth.get('totp_secret')
        totp_devicename = auth.get('totp_devicename')
        api_url = auth.get('api_url')

    strato = CertbotStratoApi(api_url)
    if not strato.login(username, password, totp_secret, totp_devicename):
        print('ERROR: Strato login not accepted.')
        sys.exit(1)
    # Requests package id which package contains domain to be verified
    strato.get_package_id()
    # Requests all current TXT/CNAME/SPF/DKIM records from Strato
    strato.get_txt_records()
    # Remove verification token record
    strato.reset_amce_record()
    # Sets all TXT/CNAME/SPF/DKIM records without AMCE record in dns server
    strato.push_txt_records()


if __name__ == '__main__':
    main()
