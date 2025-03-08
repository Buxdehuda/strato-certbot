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

    # check if environment variable exists
    if "STRATO_AUTH_ENV_ENABLE" in os.environ:
        username = os.environ.get("STRATO_USERNAME")
        password = os.environ.get("STRATO_PASSWORD")
        totp_secret = os.environ.get("STRATO_TOTP_SECRET")
        totp_devicename = os.environ.get("STRATO_TOTP_DEVICENAME")
        # parse string as int
        waiting_time = int(os.environ.get("STRATO_WAITING_TIME", 0))
        api_url = os.environ.get("STRATO_API_URL")
    else:
        print(os.environ.get("STRATO_AUTH_ENV_ENABLE"))
        # if argument exists, use it as path to strato-auth.json
        if len(sys.argv) != 2:
            print("No path to strato-auth.json provided. Using default.")
            auth_path = "strato-auth.json"
        else:
            auth_path = sys.argv[1]

        with open(
            os.path.dirname(__file__) + os.path.normcase("/" + auth_path),
            encoding="UTF-8",
        ) as file:
            auth = json.load(file)
            username = auth.get("username")
            password = auth.get("password")
            totp_secret = auth.get("totp_secret")
            totp_devicename = auth.get("totp_devicename")
            waiting_time = auth.get("waiting_time", 0)
            api_url = auth.get("api_url")

    strato = CertbotStratoApi(api_url)
    if not strato.login(username, password, totp_secret, totp_devicename):
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
    # Sleep to give the DNS Server time to get ready
    time.sleep(waiting_time)


if __name__ == "__main__":
    main()
