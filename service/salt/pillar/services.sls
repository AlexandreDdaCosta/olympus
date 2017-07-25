www_path: /srv/www

backend-user: node

backend-packages:
  mongodb-org:
    repo: jessie/mongodb-org
  nodejs:
    version: 6.11.1-2nodesource1~jessie1
  pgadmin3:
    repo: jessie-pgdg
    version: 1.22.2-1.pgdg80+1
  postgresql-9.6:
    repo: jessie-pgdg
    version: 9.6.3-1.pgdg80+1

backend-npm-packages:
  body-parser:
    version: 1.17.1
  chai:
    version: 4.0.2
  express:
    version: 4.15.0
  express-generator:
    version: 4.14.1
  fs-extra:
    version: 3.0.1
  mocha:
    version: 3.4.2
  mongodb:
    version: 2.2
  pg:
    version: 6.1.2
  pg-hstore:
    version: 2.3.2
  pm2:
    version: 2.4.2
  request:
    version: 2.81.0
  sequelize:
    version: 3.30.2
  sequelize-cli:
    version: 2.5.1
  supervisor:
    version: 0.12.0

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
  pymongo:
    version: == 3.4.0
  numpy:
    version: == 1.13.1
  freetype-py:
    version: == 1.0.2
  ipython:
    version: == 6.1.0
  nose:
    version: == 1.3.7
  pandas:
    version: == 0.20.3
  sympy:
    version: == 1.1
  jupyter:
    version: == 1.0.0
  matplotlib:
    version: == 2.0.2
  scipy:
    version: == 0.19.1

# Temporary until we start tagging releases

backend-version: 0.1

frontend-user: uwsgi

frontend-packages:
  libpq-dev:
    version: 9.6.3-1.pgdg80+1
  python3-dev:
    version: 3.4.2-2
  ruby-sass:
    version: 3.4.6-2

frontend-pip3-packages:
  django:
    version: == 1.10.6
  psycopg2:
    version: == 2.7
  uwsgi:
    version: == 2.0.14
  virtualenv:
    version: == 15.1.0

frontend-gems:
  sass:
    version: 3.4.23

web-packages:
  certbot:
    repo: jessie-backports
    version: 0.10.2-1~bpo8+1
  nginx:
    version: 1.10.3-1~jessie
