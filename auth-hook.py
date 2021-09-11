#!/usr/bin/env python3
"""Authentification hook in Certbot to Strato dns"""
import json
import os
import sys

from certbotstratoapi import CertbotStratoApi


def main():
    """Run authentification hook."""
    # get authentication data
    with open(
            os.path.dirname(__file__) + os.path.normcase("/strato-auth.json"),
            encoding='UTF-8',
            ) as file:
        auth = json.load(file)
        username = auth['username']
        password = auth['password']

    strato = CertbotStratoApi()
    if not strato.login(username, password):
        print("ERROR: Strato login not accepted.")
        sys.exit(1)
    # Requests package id which package contains domain to be verified
    strato.get_package_id()
    # Requests all current TXT/CNAME/SPF/DKIM records from Strato
    strato.get_txt_records()
    # Add verification token record
    strato.set_amce_record()
    # Sets all TXT/CNAME/SPF/DKIM records with AMCE record in dns server
    strato.push_txt_records()


if __name__ == "__main__":
    main()
