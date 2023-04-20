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
    version: 2.10.4+dfsg-1+deb11u1
  liblapack-dev:
    version: 3.9.0-3
  pkg-config:
    version: 0.29.2-1

bigdata-pip3-packages:
  numpy:
    version: == 1.24.2
  freetype-py:
    version: == 2.3.0
  ipython:
    version: == 8.12.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 2.0.0
  sympy:
    version: == 1.11.1
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 3.7.1
  scipy:
    version: == 1.10.1

pip3-packages:
  jsonschema:
    version: == 4.17.3
  pycodestyle:
    version: == 2.10.0
  pymongo:
    version: == 4.3.3
  wget:
    version: == 3.2

web-packages:
  certbot:
    repo: {{ release_name }}-backports
    version: 1.12.0-2
  nginx:
    version: 1.24.0-1~bullseye
