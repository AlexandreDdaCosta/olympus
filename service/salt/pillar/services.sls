{% from 'distribution.sls' import release_name %}

frontend-user: uwsgi
www_path: /srv/www

bigdata-packages:
  gfortran:
    version: 4:10.2.1-1
  gfortran-multilib:
    version: 4:10.2.1-1
  libblas-dev:
    version: 3.9.0-3
  libfreetype6-dev:
    version: 2.10.4+dfsg-1
  liblapack-dev:
    version: 3.9.0-3
  pkg-config:
    version: 0.29.2-1

bigdata-pip3-packages:
  numpy:
    version: == 1.22.3
  freetype-py:
    version: == 2.2.0
  ipython:
    version: == 8.2.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 1.4.2
  sympy:
    version: == 1.10.1
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 3.5.1
  scipy:
    version: == 1.8.0

pip3-packages:
  jsonschema:
    version: == 4.4.0
  pymongo:
    version: == 4.1.0
  wget:
    version: == 3.2

web-packages:
  certbot:
    repo: {{ release_name }}-backports
    version: 1.12.0-2
  nginx:
    version: 1.20.2-1~buster
