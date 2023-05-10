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

`sudo chmod 0400 strato-auth.json`

### Two-Factor Authentification

To be able to authenticate two-factor, device name and TOTP secret must be entered into the JSON. If it is not used, it can either be empty strings or the entries can be removed completely (see above).

```json
{
  "username": "<username>",
  "password": "<password>",
  "totp_secret": "<secret>",
  "totp_devicename": "<devicename>"
}
```

### Waiting time

Sometimes it takes a while until the desired DNS record is published, which allows Certbot to verify the domain. To prevent this, a waiting time can be set.

```json
{
  "username": "<username>",
  "password": "<password>",
  "waiting_time": <seconds>
}
```

## Get certificate

Run Certbot in manual mode:

`sudo certbot certonly --manual --preferred-challenges dns --manual-auth-hook $(pwd)/auth-hook.py --manual-cleanup-hook $(pwd)/cleanup-hook.py -d example.com -d *.example.com`

This will generate a wildcard certificate for your domain without the need to manually enter the TXT records.

## Docker

The Dockerfile wraps these hook scripts into a certbot runtime

### Setup

Edit and copy the certbot.env.sample to certbot.env

### Build

Run `./build.sh`

### Run

Run `./run.sh`

### Get certificates

A docker volume named "letsencrypt" will be created, the certificates can be found there ( `docker volume inspect letsencrypt` )
