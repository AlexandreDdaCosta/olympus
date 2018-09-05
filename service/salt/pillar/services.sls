www_path: /srv/www

backend-user: node

backend-packages:
  mongodb-org:
    repo: jessie/mongodb-org
  nodejs:
    version: 6.14.4-1nodesource1~jessie1
  pgadmin3:
    repo: jessie-pgdg
    version: 1.22.2-4.pgdg80+1
  postgresql-9.6:
    repo: jessie-pgdg
    version: 9.6.10-1.pgdg80+1

backend-npm-packages:
  body-parser:
    version: 1.18.3
  chai:
    version: 4.1.2
  express:
    version: 4.16.3
  express-generator:
    version: 4.16.0
  fs-extra:
    version: 7.0.0
  mocha:
    version: 5.2.0
  mongodb:
    version: 3.1.4
  pg:
    version: 7.4.3
  pg-hstore:
    version: 2.3.2
  pm2:
    version: 3.0.4
  request:
    version: 2.88.0
  sequelize:
    version: 4.38.0
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

# Temporary until we start tagging releases

backend-version: 0.1

frontend-user: uwsgi

frontend-packages:
  libpq-dev:
    version: 10.5-1.pgdg80+1
  python3-dev:
    version: 3.4.2-2
  ruby-sass:
    version: 3.4.6-2

frontend-pip3-packages:
  django:
    version: == 2.1.1
  psycopg2:
    version: == 2.7.5
  uwsgi:
    version: == 2.0.17.1
  virtualenv:
    version: == 16.0.0

frontend-gems:
  sass:
    version: 3.4.6

web-packages:
  certbot:
    repo: jessie-backports
    version: 0.10.2-1~bpo8+1
  nginx:
    version: 1.14.0-1~jessie
