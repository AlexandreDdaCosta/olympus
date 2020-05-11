{% from 'distribution.sls' import release-name %}

backend-user: node
# Temporary until we start tagging releases
backend-version: 0.1

backend-packages:
  mongodb-org:
    repo: {{ release-name }}/mongodb-org
  nodejs:
    version: 10.20.1-1nodesource1
  pgadmin3:
    repo: {{ release1name }}-pgdg
    version: 1.22.2-6.pgdg90+2
  postgresql-9.6:
    repo: {{ release-name }}-pgdg
    version: 9.6.17-2.pgdg90+1

backend-npm-packages:
  body-parser:
    version: 1.19.0
  chai:
    version: 4.2.0
  express:
    version: 4.17.1
  express-generator:
    version: 4.16.1
  fs-extra:
    version: 9.0.0
  mocha:
    version: 7.1.2
  mongodb:
    version: 3.5.7
  pg:
    version: 8.1.0
  pg-hstore:
    version: 2.3.3
  pm2:
    version: 4.4.0
  request:
    version: 2.88.2
  sequelize:
    version: 5.21.8
  sequelize-cli:
    version: 5.5.1
  supervisor:
    version: 0.12.0

