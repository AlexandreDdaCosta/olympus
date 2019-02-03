{% from 'distribution.sls' import release_name %}

frontend-user: uwsgi
www_path: /srv/www

bigdata-packages:
  gfortran:
    version: 4:6.3.0-4
  gfortran-multilib:
    version: 4:6.3.0-4
  libblas-dev:
    version: 3.7.0-2
  libfreetype6-dev:
    version: 2.6.3-3.2
  liblapack-dev:
    version: 3.7.0-2
  pkg-config:
    version: 0.29-4+b1

bigdata-pip3-packages:
  wget:
    version: == 3.2
  pymongo:
    version: == 3.7.2
  numpy:
    version: == 1.16.1
  freetype-py:
    version: == 2.0.0.post6
  ipython:
    version: == 7.2.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 0.24.0
  sympy:
    version: == 1.3
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 3.0.2
  scipy:
    version: == 1.2.0

web-packages:
  certbot:
    repo: {{ release_name }}-backports
    version: 0.28.0-1~bpo9+1
  nginx:
    version: 1.14.2-1~stretch
