#!/bin/bash
docker run --env-file certbot.env --rm -v letsencrypt:/etc/letsencrypt stratobot 
