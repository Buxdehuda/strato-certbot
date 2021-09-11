"""Certbot-Strato-API Class"""
import os
import re
import sys

import requests


class CertbotStratoApi:
    """Class to validate domains for Certbot with dns-01 challange"""

    def __init__(self):
        """ Initializes the data structure """
        self.api_url = "https://www.strato.de/apps/CustomerService"
        self.txt_key = "_acme-challenge"
        self.txt_value = os.environ['CERTBOT_VALIDATION']
        self.domain_name = os.environ['CERTBOT_DOMAIN']
        self.second_level_domain_name = re.search(r'(\w+\.\w+)$',
            self.domain_name).group(1)

        print('INFO: txt_key: %s' % (self.txt_key))
        print('INFO: txt_value: %s' % (self.txt_value))
        print('INFO: second_level_domain_name: %s'
            % (self.second_level_domain_name))
        print('INFO: domain_name: %s' % (self.domain_name))

        # setup session for cookie sharing
        self.http_session = requests.session()

        # Set later
        self.session_id = ''
        self.package_id = 0
        self.records = []


    def login(self, username: str, password: str) -> bool:
        """Login to Strato website. Requests session ID.

        :param str username: Username or customer number of
                "STRATO Customer Login"
        :param str password: Password of "STRATO Customer Login"

        :returns: Successful login
        :rtype: bool

        """
        # request session id
        request = self.http_session.get(self.api_url)
        request = self.http_session.post(self.api_url, {
            'identifier': username,
            'passwd': password,
            'action_customer_login.x': "Login"
        })
        result = re.search(r'sessionID=(\w+)', request.url)
        if not result:
            return False
        self.session_id = result.group(1)
        print('DEBUG: session_id: %s' % (self.session_id))
        return True


    def get_package_id(self) -> None:
        """Requests package ID for the selected domain."""
        # request strato packages
        request = self.http_session.get(self.api_url, params={
            'sessionID': self.session_id,
            'cID': 0,
            'node': "kds_CustomerEntryPage",
        })
        result = re.search(
            r'<div class="cep_product">\s*<a class="customer-link" href='
            r'"[^"]*cID=(?P<cID>\d+).*<span [^>]*>[^\/]*'
            + self.second_level_domain_name.replace('.', r'\.'),
            request.text
            )

        if result is None:
            print('ERROR: Domain %s not found in strato packages'
                % (self.second_level_domain_name))
            sys.exit(1)
        self.package_id = result.group("cID")
        print('INFO: strato package id (cID): ' + self.package_id)


    def get_txt_records(self) -> None:
        """Requests all txt and cname records related to domain."""
        request = self.http_session.get(self.api_url, params={
            'sessionID': self.session_id,
            'cID': self.package_id,
            'node': "ManageDomains",
            'action_show_txt_records': '',
            'vhost': self.domain_name
        })
        for record in re.finditer(
                r'<input [^>]*value="(?P<prefix>[^"]*)"[^>]*'
                r'name="prefix"[^>]*>.*<select [^>]*name="type"[^>]*>.*'
                r'<option[^>]*value="(?P<type>[^"]*)"[^>]*selected[^>]*>.*'
                r'</select>.*<textarea [^>]*name="value"[^>]*>(?P<value>.*)'
                r'</textarea>',
                request.text):
            self.records.append({
                'prefix': record.group('prefix'),
                'type': record.group('type'),
                'value': record.group('value')
            })

        print('INFO: Current cname/txt records:')
        list(print("INFO: - %s %s: %s"%(
            item['prefix'],item['type'],item['value']))
            for item in self.records)


    def add_txt_record(self, prefix: str, record_type: str, value: str) -> None:
        """Add a txt/cname record.

        :param prefix str: Prefix of record
        :param record_type str: Type of record ('TXT' or 'CNAME')
        :param value str: Value of record

        """
        self.records.append({
            'prefix': prefix,
            'type': record_type,
            'value': value,
        })


    def remove_txt_record(self, prefix: str, record_type: str) -> None:
        """Add a txt/cname record.

        :param prefix str: Prefix of record
        :param record_type str: Type of record ('TXT' or 'CNAME')

        """
        for i in reversed(range(len(self.records))):
            if (self.records[i]['prefix'] == prefix
                and self.records[i]['type'] == record_type):
                self.records.pop(i)


    def set_amce_record(self) -> None:
        """Set or replace AMCE txt record on domain."""
        self.remove_txt_record(self.txt_key, 'TXT')
        self.add_txt_record(self.txt_key, 'TXT', self.txt_value)


    def reset_amce_record(self) -> None:
        """Reset AMCE txt record on domain."""
        self.remove_txt_record(self.txt_key, 'TXT')


    def push_txt_records(self) -> None:
        """Push modified txt records to Strato."""
        print('INFO: New cname/txt records:')
        list(print("INFO: - %s %s: %s"%(item['prefix'],item['type'],item['value']))
            for item in self.records)

        self.http_session.post(self.api_url, {
            'sessionID': self.session_id,
            'cID': self.package_id,
            'node': "ManageDomains",
            'vhost': self.domain_name,
            'spf_type': "NONE",
            'prefix': [r['prefix'] for r in self.records],
            'type': [r['type'] for r in self.records],
            'value': [r['value'] for r in self.records],
            'action_change_txt_records': "Einstellung+übernehmen",
        })
