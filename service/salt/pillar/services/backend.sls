{% from 'distribution.sls' import release_name %}

backend-user: node
# Temporary until we start tagging releases
backend-version: 0.1

backend-packages:
  mongodb-org:
    repo: {{ release_name }}/mongodb-org
  nodejs:
    version: 10.15.1-1nodesource1
  pgadmin3:
    repo: {{ release_name }}-pgdg
    version: 1.22.2-4.pgdg90+1
  postgresql-9.6:
    repo: {{ release_name }}-pgdg
    version: 9.6.11-1.pgdg90+1

backend-npm-packages:
  body-parser:
    version: 1.18.3
  chai:
    version: 4.2.0
  express:
    version: 4.16.4
  express-generator:
    version: 4.16.0
  fs-extra:
    version: 7.0.1
  mocha:
    version: 5.2.0
  mongodb:
    version: 3.1.13
  pg:
    version: 7.8.0
  pg-hstore:
    version: 2.3.2
  pm2:
    version: 3.2.9
  request:
    version: 2.88.0
  sequelize:
    version: 4.42.0
  sequelize-cli:
    version: 5.4.0
  supervisor:
    version: 0.12.0

