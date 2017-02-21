web-service-packages:
  certbot:
    fromrepo: jessie-backports
    version: foo
  nginx:
    version: 1.10.3-1~jessie
  python2.7-dev:
    version: 2.7.9-2+deb8u1

web-service-pip-packages:
  uwsgi:
    version: == 2.0.14
