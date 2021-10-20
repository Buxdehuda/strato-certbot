#!/usr/bin/env python3
"""Authentification hook in Certbot to Strato dns"""
import json
import os
import sys
import time

from certbotstratoapi import CertbotStratoApi


def main():
    """Run authentification hook."""
    # get authentication data
    with open(
            os.path.dirname(__file__) + os.path.normcase('/strato-auth.json'),
            encoding='UTF-8',
            ) as file:
        auth = json.load(file)
        username = auth.get('username')
        password = auth.get('password')
        totp_secret = auth.get('totp_secret')
        totp_devicename = auth.get('totp_devicename')

    strato = CertbotStratoApi()
    if not strato.login(username, password, totp_secret, totp_devicename):
        print('ERROR: Strato login not accepted.')
        sys.exit(1)
    # Requests package id which package contains domain to be verified
    strato.get_package_id()
    # Requests all current TXT/CNAME/SPF/DKIM records from Strato
    strato.get_txt_records()
    # Add verification token record
    strato.set_amce_record()
    # Sets all TXT/CNAME/SPF/DKIM records with AMCE record in dns server
    strato.push_txt_records()
    # Sleep 10 Seconds to give the DNS Server time to get ready
    time.sleep(10)


if __name__ == '__main__':
    main()
