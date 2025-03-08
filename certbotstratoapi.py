"""Certbot-Strato-API Class"""

import os
import re
import urllib

import pyotp
import requests
from bs4 import BeautifulSoup


class CertbotStratoApi:
    """Class to validate domains for Certbot with dns-01 challange"""

    def __init__(self, api_url=None):
        """Initializes the data structure"""
        if api_url is None:
            self.api_url = "https://www.strato.de/apps/CustomerService"
        else:
            self.api_url = api_url
        self.txt_key = "_acme-challenge"
        self.txt_value = os.environ["CERTBOT_VALIDATION"]
        self.domain_name = os.environ["CERTBOT_DOMAIN"]
        self.second_level_domain_name = re.search(
            r"([\w-]+\.[\w-]+)$", self.domain_name
        ).group(1)
        self.subdomain = self.extract_subdomain()
        print(f"INFO: txt_key: {self.txt_key}")
        print(f"INFO: txt_value: {self.txt_value}")
        print(f"INFO: second_level_domain_name: {self.second_level_domain_name}")
        print(f"INFO: domain_name: {self.domain_name}")
        print(f"INFO: subdomain: {self.subdomain}")

        # setup session for cookie sharing
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0"
        }
        self.http_session = requests.session()
        self.http_session.headers.update(headers)

        # Set later
        self.session_id = ""
        self.package_id = 0
        self.records = []

    def login_2fa(
        self,
        response: requests.Response,
        username: str,
        totp_secret: str,
        totp_devicename: str,
    ) -> requests.Response:
        """Login with Two-factor authentication by TOTP on Strato website.

        :param str totp_secret: 2FA TOTP secret hash
        :param str totp_devicename: 2FA TOTP device name

        :returns: Original response or 2FA response
        :rtype: requests.Response

        """
        # Is 2FA used
        soup = BeautifulSoup(response.text, "html.parser")
        if (
            soup.find("h1", string=re.compile("Zwei\\-Faktor\\-Authentifizierung"))
            is None
        ):
            print("INFO: 2FA is not used.")
            return response
        if (not totp_secret) or (not totp_devicename):
            print("ERROR: 2FA parameter is not completely set.")
            return response

        param = {"identifier": username}

        # Set parameter 'totp_token'
        totp_input = soup.find("input", attrs={"type": "hidden", "name": "totp_token"})
        if totp_input is not None:
            param["totp_token"] = totp_input["value"]
        else:
            print("ERROR: Parsing error on 2FA site by totp_token.")
            return response

        # Set parameter 'action_customer_login.x'
        param["action_customer_login.x"] = 1

        # No idea what this regex does
        # TODO: rewrite with beautifulsoup
        # Set parameter pw_id
        for device in re.finditer(
            rf'<option value="(?P<value>(S\.{username}\.\w*))"'
            r'( selected(="selected")?)?\s*>(?P<name>(.+?))</option>',
            response.text,
        ):
            if totp_devicename.strip() == device.group("name").strip():
                param["pw_id"] = device.group("value")
                break
        if param.get("pw_id") is None:
            print("ERROR: Parsing error on 2FA site by device name.")
            return response

        # Set parameter 'totp'
        param["totp"] = pyotp.TOTP(totp_secret).now()
        print(f'DEBUG: totp: {param.get("totp")}')

        request = self.http_session.post(self.api_url, param)
        return request

    def login(
        self,
        username: str,
        password: str,
        totp_secret: str = None,
        totp_devicename: str = None,
    ) -> bool:
        """Login to Strato website. Requests session ID.

        :param str username: Username or customer number of
                'STRATO Customer Login'
        :param str password: Password of 'STRATO Customer Login'
        :param str totp-secret: 2FA TOTP secret hash
        :param str totp-devicename: 2FA TOTP device name

        :returns: Successful login
        :rtype: bool

        """
        # request session id
        self.http_session.get(self.api_url)
        data = {
            "identifier": username,
            "passwd": password,
            "action_customer_login.x": "Login",
        }

        request = self.http_session.post(self.api_url, data=data)

        # Check 2FA Login
        request = self.login_2fa(request, username, totp_secret, totp_devicename)

        # Check successful login
        parsed_url = urllib.parse.urlparse(request.url)
        query_parameters = urllib.parse.parse_qs(parsed_url.query)
        if "sessionID" not in query_parameters:
            return False
        self.session_id = query_parameters["sessionID"][0]
        print(f"DEBUG: session_id: {self.session_id}")
        return True

    def get_package_id(self) -> None:
        """Requests package ID for the selected domain."""
        # request strato packages
        request = self.http_session.get(
            self.api_url,
            params={
                "sessionID": self.session_id,
                "cID": 0,
                "node": "kds_CustomerEntryPage",
            },
        )
        soup = BeautifulSoup(request.text, "html.parser")
        package_anchor = soup.select_one(
            "#package_list > tbody >"
            f' tr:has(.package-information:-soup-contains("{self.second_level_domain_name}"))'
            " .jss_with_own_packagename a"
        )
        if package_anchor:
            if package_anchor.has_attr("href"):
                link_target = urllib.parse.urlparse(package_anchor["href"])
                self.package_id = urllib.parse.parse_qs(link_target.query)["cID"][0]
                print(f"INFO: strato package id (cID): {self.package_id}")
                return

        print(
            f"ERROR: Domain {self.second_level_domain_name} not "
            "found in strato packages. Using fallback cID=1"
        )
        self.package_id = 1

    def extract_subdomain(self) -> str:
        if self.domain_name == self.second_level_domain_name:
            return ""
        if self.domain_name.endswith(self.second_level_domain_name):
            # Compatibility with Python versions before 3.9: using
            # len()-based method instead of removesuffix()
            subdomain = self.domain_name[: -len("." + self.second_level_domain_name)]
            return subdomain
        raise ValueError(
            f"Domain name {self.domain_name} does not end with {self.second_level_domain_name}"
        )

    def get_txt_records(self) -> None:
        """Requests all txt and cname records related to domain."""
        request = self.http_session.get(
            self.api_url,
            params={
                "sessionID": self.session_id,
                "cID": self.package_id,
                "node": "ManageDomains",
                "action_show_txt_records": "",
                "vhost": self.domain_name,
            },
        )
        # No idea what this regex does
        # TODO: rewrite with beautifulsoup
        for record in re.finditer(
            r'<select [^>]*name="type"[^>]*>.*?'
            r'<option[^>]*value="(?P<type>[^"]*)"[^>]*selected[^>]*>'
            r".*?</select>.*?"
            r'<input [^>]*value="(?P<prefix>[^"]*)"[^>]*name="prefix"[^>]*>'
            r'.*?<textarea [^>]*name="value"[^>]*>(?P<value>.*?)</textarea>',
            request.text,
        ):
            self.records.append(
                {
                    "prefix": record.group("prefix"),
                    "type": record.group("type"),
                    "value": record.group("value"),
                }
            )

        print("INFO: Current cname/txt records:")
        list(
            print(f'INFO: - {item["prefix"]} {item["type"]}: {item["value"]}')
            for item in self.records
        )

    def add_txt_record(self, prefix: str, record_type: str, value: str) -> None:
        """Add a txt/cname record.

        :param prefix str: Prefix of record
        :param record_type str: Type of record ('TXT' or 'CNAME')
        :param value str: Value of record

        """
        self.records.append(
            {
                "prefix": prefix,
                "type": record_type,
                "value": value,
            }
        )

    def remove_txt_record(self, prefix: str, record_type: str) -> None:
        """Remove a txt/cname record.

        :param prefix str: Prefix of record
        :param record_type str: Type of record ('TXT' or 'CNAME')

        """
        for i in reversed(range(len(self.records))):
            if (
                self.records[i]["prefix"] == prefix
                and self.records[i]["type"] == record_type
            ):
                self.records.pop(i)

    def set_amce_record(self) -> None:
        """Set or replace AMCE txt record on domain."""
        key = f"{self.txt_key}.{self.subdomain}" if self.subdomain else self.txt_key
        self.add_txt_record(key, "TXT", self.txt_value)

    def reset_amce_record(self) -> None:
        """Reset AMCE txt record on domain."""
        key = f"{self.txt_key}.{self.subdomain}" if self.subdomain else self.txt_key
        self.remove_txt_record(key, "TXT")

    def push_txt_records(self) -> None:
        """Push modified txt records to Strato."""
        print("INFO: New cname/txt records:")
        list(
            print(f'INFO: - {item["prefix"]} {item["type"]}: {item["value"]}')
            for item in self.records
        )

        self.http_session.post(
            self.api_url,
            {
                "sessionID": self.session_id,
                "cID": self.package_id,
                "node": "ManageDomains",
                "vhost": self.domain_name,
                "spf_type": "NONE",
                "prefix": [r["prefix"] for r in self.records],
                "type": [r["type"] for r in self.records],
                "value": [r["value"] for r in self.records],
                "action_change_txt_records": "Einstellung+übernehmen",
            },
        )
