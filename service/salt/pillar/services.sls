{% from 'distribution.sls' import release_name %}

frontend-user: uwsgi
www_path: /srv/www

bigdata-packages:
  gfortran:
    version: 4:8.3.0-1
  gfortran-multilib:
    version: 4:8.3.0-1
  libblas-dev:
    version: 3.8.0-2
  libfreetype6-dev:
    version: 2.9.1-3+deb10u2
  liblapack-dev:
    version: 3.8.0-2
  pkg-config:
    version: 0.29-6

bigdata-pip3-packages:
  numpy:
    version: == 1.20.1
  freetype-py:
    version: == 2.2.0
  ipython:
    version: == 7.21.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 1.2.2
  sympy:
    version: == 1.7.1
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 3.3.4
  scipy:
    version: == 1.6.1

pip3-packages:
  jsonschema:
    version: == 3.2.0
  pymongo:
    version: == 3.11.3
  wget:
    version: == 3.2

web-packages:
  certbot:
    repo: {{ release_name }}-backports
    version: 0.31.0-1+deb10u1
  nginx:
    version: 1.18.0-2~buster
