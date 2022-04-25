{% from 'distribution.sls' import release_name %}

backend-user: node
# Temporary until we start tagging releases
backend-version: 0.1

backend-packages:
  mongodb-org:
    repo: {{ release_name }}/mongodb-org
  nodejs:
    version: 16.14.2-deb-1nodesource1
  pgadmin3:
    repo: {{ release_name }}-pgdg
    version: 1.22.2-6.pgdg100+2
  postgresql-14:
    repo: {{ release_name }}-pgdg
    version: 14.2-1.pgdg110+1

backend-npm-packages:
  body-parser:
    version: 1.20.0
  chai:
    version: 4.3.6
  express:
    version: 4.17.3
  express-generator:
    version: 4.16.1
  fs-extra:
    version: 10.0.1
  jest:
    version: 27.5.1
  mongodb:
    version: 4.5.0
  pg:
    version: 8.7.3
  pg-hstore:
    version: 2.3.4
  pm2:
    version: 5.2.0
  request:
    version: 2.88.2
  sequelize:
    version: 6.18.0
  sequelize-cli:
    version: 6.4.1
  supervisor:
    last_entry: True
    version: 0.12.0
