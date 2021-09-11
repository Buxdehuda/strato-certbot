#!/usr/bin/env python3
import json
import os
import re

import requests


def main():
    # get authentication
    with open(os.path.dirname(__file__) + os.path.normcase("/strato-auth.json")) as file:
        auth = json.load(file)
        username = auth['username']
        password = auth['password']

    api_url = "https://www.strato.de/apps/CustomerService"
    txt_key = "_acme-challenge"
    txt_value = os.environ['CERTBOT_VALIDATION']
    domain_name = os.environ['CERTBOT_DOMAIN']
    second_level_domain_name = re.search(r'(\w+\.\w+)$', domain_name).group(1)

    print('INFO: txt_key: %s' % (txt_key))
    print('INFO: txt_value: %s' % (txt_value))
    print('INFO: second_level_domain_name: %s' % (second_level_domain_name))
    print('INFO: domain_name: %s' % (domain_name))

    # setup session for cookie sharing
    http_session = requests.session()

    # request session id
    request = http_session.get(api_url)
    request = http_session.post(api_url, {
        'identifier': username,
        'passwd': password,
        'action_customer_login.x': "Login"
    })
    result = re.search(r'sessionID=(\w+)', request.url)
    if not result:
        print("ERROR: Strato login not accepted.")
        exit(1)
    session_id = result.group(1)
    print('DEBUG: session_id: %s' % (session_id))

    # request strato packages
    request = http_session.get(api_url, params={
        'sessionID': session_id,
        'cID': 0,
        'node': "kds_CustomerEntryPage"
    })
    m = re.search(r'<div class="cep_product">\s*<a class="customer-link" href="[^"]*cID=(?P<cID>\d+)'
                  r'.*<span [^>]*>[^\/]*' + second_level_domain_name.replace('.', '\.'), request.text)
    if m is None:
        print('ERROR: Domain %s not found in strato packages' % (domain_name))
        exit(1)
    cID = m.group("cID")
    print('INFO: strato package id (cID): ' + cID)

    # request current cname/txt records
    request = http_session.get(api_url, params={
        'sessionID': session_id,
        'cID': cID,
        'node': "ManageDomains",
        'action_show_txt_records': '',
        'vhost': domain_name
    })
    records = []
    for m in re.finditer(r'<input [^>]*value="(?P<prefix>[^"]*)"[^>]*name="prefix"[^>]*>.*'
                         r'<select [^>]*name="type"[^>]*>.*'
                         r'<option[^>]*value="(?P<type>[^"]*)"[^>]*selected[^>]*>.*'
                         r'</select>.*'
                         r'<textarea [^>]*name="value"[^>]*>(?P<value>.*)</textarea>', request.text):
        records.append({
            'prefix': m.group('prefix'),
            'type': m.group('type'),
            'value': m.group('value')
        })

    print('INFO: Current cname/txt records:')
    [print("INFO: - %s %s: %s"%(item['prefix'],item['type'],item['value'])) for item in records]

    # add/replace txt record
    for i in reversed(range(len(records))):
        if records[i]['prefix'] == txt_key and records[i]['type'] == "TXT":
            records.pop(i)

    records.append({
        'prefix': txt_key,
        'type': "TXT",
        'value': txt_value,
    })

    print('INFO: New cname/txt records:')
    [print("INFO: - %s %s: %s"%(item['prefix'],item['type'],item['value'])) for item in records]

    # set records
    http_session.post(api_url, {
        'sessionID': session_id,
        'cID': cID,
        'node': "ManageDomains",
        'vhost': domain_name,
        'spf_type': "NONE",
        'prefix': [r['prefix'] for r in records],
        'type': [r['type'] for r in records],
        'value': [r['value'] for r in records],
        'action_change_txt_records': "Einstellung+übernehmen"
    })


if __name__ == "__main__":
    main()
