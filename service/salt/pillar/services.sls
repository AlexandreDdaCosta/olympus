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
    version: 2.9.1-3+deb10u1
  liblapack-dev:
    version: 3.8.0-2
  pkg-config:
    version: 0.29-6

bigdata-pip3-packages:
  numpy:
    version: == 1.19.0
  freetype-py:
    version: == 2.2.0
  ipython:
    version: == 7.16.1
  nose:
    version: == 1.3.7
  pandas:
    version: == 1.0.5
  sympy:
    version: == 1.6.1
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 3.3.0
  scipy:
    version: == 1.5.1

pip3-packages:
  pymongo:
    version: == 3.10.1
  wget:
    version: == 3.2

web-packages:
  certbot:
    repo: {{ release_name }}-backports
    version: 0.31.0-1
  nginx:
    version: 1.18.0-1~buster
