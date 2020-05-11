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
    version: 2.6.3-3.2+deb9u1
  liblapack-dev:
    version: 3.7.0-2
  pkg-config:
    version: 0.29-4+b1

bigdata-pip3-packages:
  wget:
    version: == 3.2
  pymongo:
    version: == 3.10.1
  numpy:
    version: == 1.18.4
  freetype-py:
    version: == 2.1.0.post1
  ipython:
    version: == 7.9.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 0.25.3
  sympy:
    version: == 1.5.1
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 3.0.3
  scipy:
    version: == 1.4.1

web-packages:
  certbot:
    repo: {{ release_name }}-backports
    version: 0.28.0-1~deb9u2
  nginx:
    version: 1.18.0-1~stretch
