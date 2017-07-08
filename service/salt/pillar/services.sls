www_path: /srv/www

backend-user: node

backend-packages:
  mongodb-org:
    repo: jessie/mongodb-org/3.4
  nodejs:
    version: 6.10.0-1nodesource1~jessie1
  pgadmin3:
    repo: jessie-pgdg
    version: 1.22.2-1.pgdg80+1
  postgresql-9.6:
    repo: jessie-pgdg
    version: 9.6.2-1.pgdg80+1

backend-npm-packages:
  body-parser:
    version: 1.17.1
  chai:
    version: 4.0.2
  express:
    version: 4.15.0
  express-generator:
    version: 4.14.1
  mocha:
    version: 3.4.2
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

frontend-user: uwsgi

frontend-packages:
  libpq-dev:
    version: 9.6.2-1.pgdg80+1
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
    version: 0.9.3-1~bpo8+2
  nginx:
    version: 1.10.3-1~jessie
