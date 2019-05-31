# strato-certbot
Wildcard certificates for strato.de

## Setup

Create `strato-auth.json`:

```json
{
  "username": "<username>",
  "password": "<password>"
}
```

Make sure to make this file only readable for root:

`sudo chmod 0400 ./strato-auth.json`

## Get certificate

Run Certbot in manual mode:

`sudo certbot certonly --manual --preferred-challenges dns --manual-auth-hook ./auth-hook.py -d example.com -d *.example.com`

This will generate a wildcard certificate for your domain without the need to manually enter the TXT records.

__NOTE:__ The python files need to be referenced by the absolute path if you want to use `certbot renew`
