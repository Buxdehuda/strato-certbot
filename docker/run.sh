#!/bin/bash
docker run --env-file certbot.env --env-file auth.env --rm -v letsencrypt:/etc/letsencrypt stratobot
