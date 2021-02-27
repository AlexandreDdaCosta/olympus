{% from 'distribution.sls' import release_name %}

backend-user: node
# Temporary until we start tagging releases
backend-version: 0.1

backend-packages:
  mongodb-org:
    repo: {{ release_name }}/mongodb-org
  nodejs:
    version: 14.16.0-1nodesource1
  pgadmin3:
    repo: {{ release_name }}-pgdg
    version: 1.22.2-6.pgdg100+2
  postgresql-9.6:
    repo: {{ release_name }}-pgdg
    version: 9.6.21-1.pgdg100+1

backend-npm-packages:
  body-parser:
    version: 1.19.0
  chai:
    version: 4.3.0
  express:
    version: 4.17.1
  express-generator:
    version: 4.16.1
  fs-extra:
    version: 9.1.0
  mocha:
    version: 8.3.0
  mongodb:
    version: 3.5.9
  pg:
    version: 8.5.1
  pg-hstore:
    version: 2.3.3
  pm2:
    version: 4.5.5
  request:
    version: 2.88.2
  sequelize:
    version: 6.5.0
  sequelize-cli:
    version: 6.2.0
  supervisor:
    version: 0.12.0

