FROM python:3-alpine as test
Add ../ ./
RUN pip install --no-cache-dir -r requirements-dev.txt
RUN python -m pytest ./test 

FROM certbot/certbot
Add ../ ./
RUN chmod +x *.py
RUN pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT ["sh",  "-c", "certbot certonly --agree-tos --no-eff-email --email $EMAIL --manual --preferred-challenges dns --manual-auth-hook /opt/certbot/auth-hook.py --manual-cleanup-hook /opt/certbot/cleanup-hook.py -d $DOMAIN -d *.$DOMAIN"]
