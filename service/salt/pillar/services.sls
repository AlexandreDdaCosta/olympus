web-service-packages:
  certbot:
    repo: jessie-backports
    version: 0.9.3-1~bpo8+2
  nginx:
    version: 1.10.3-1~jessie

nodejs-web-service-packages:
  nodejs:
    version: 6.10.0-1nodesource1~jessie1

nodejs-web-service-npm-packages:
  express:
    version: 4.15.0
  express-generator:
    version: 4.14.1
  pg:
    version: 6.1.2
  pm2:
    version: 2.4.2
  supervisor:
    version: 0.12.0

python-web-service-packages:
  python2.7-dev:
    version: 2.7.9-2+deb8u1

python-web-service-pip-packages:
  uwsgi:
    version: == 2.0.14

python-web-service-pip3-packages:
  django:
  virtualenv:
    version: == 15.1.0
