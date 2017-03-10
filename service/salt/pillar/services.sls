backend-packages:
  nodejs:
    version: 6.10.0-1nodesource1~jessie1
  pgadmin3:
    repo: jessie-pgdg
    version: 1.22.2-1.pgdg80+1
  postgresql-9.6:
    repo: jessie-pgdg
    version: 9.6.2-1.pgdg80+1

backend-npm-packages:
  express:
    version: 4.15.0
  express-generator:
    version: 4.14.1
  pg:
    version: 6.1.2
  pg-hstore:
    version: 2.3.2
  pm2:
    version: 2.4.2
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
  python2.7-dev:
    version: 2.7.9-2+deb8u1
  python3-dev:
    version: 3.4.2-2

frontend-pip3-packages:
  django:
    version: == 1.10.6
  psycopg2:
    version: == 2.7
  uwsgi:
    version: == 2.0.14
  virtualenv:
    version: == 15.1.0

web-packages:
  certbot:
    repo: jessie-backports
    version: 0.9.3-1~bpo8+2
  nginx:
    version: 1.10.3-1~jessie
