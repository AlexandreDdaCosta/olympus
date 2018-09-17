frontend-user: uwsgi
{% set web_path = '/srv/www' %}
www_path: {{ web_path }}

bigdata-packages:
  gfortran:
    version: 4:4.9.2-2
  gfortran-multilib:
    version: 4:4.9.2-2
  libblas-dev:
    version: 1.2.20110419-10
  libfreetype6-dev:
    version: 2.5.2-3+deb8u2
  liblapack-dev:
    version: 3.5.0-4
  pkg-config:
    version: 0.28-1

bigdata-pip3-packages:
  wget:
    version: == 3.2
  pymongo:
    version: == 3.7.1
  numpy:
    version: == 1.15.1
  freetype-py:
    version: == 2.0.0.post6
  ipython:
    version: == 6.5.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 0.23.4
  sympy:
    version: == 1.2
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 2.2.3
  scipy:
    version: == 1.1.0

web-packages:
  certbot:
    repo: jessie-backports
    version: 0.10.2-1~bpo8+1
  nginx:
    version: 1.14.0-1~jessie
