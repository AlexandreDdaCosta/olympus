{% from 'distribution.sls' import release_name %}

backend-user: node
# Temporary until we start tagging releases
backend-version: 0.1

backend-packages:
  nodejs:
    version: 16.20.0-deb-1nodesource1
  pgadmin3:
    repo: {{ release_name }}-pgdg
    version: 1.22.2-6.pgdg100+2
  postgresql-14:
    repo: {{ release_name }}-pgdg
    version: 14.7-1.pgdg110+1

backend-npm-packages:
  argon2:
    version: 0.30.3
  async:
    version: 3.2.4
  body-parser:
    version: 1.20.2
  chai:
    version: 4.3.7
  config:
    version: 3.3.9
  corepack:
    version: 0.17.2
  cors:
    version: 2.8.5
  crypto:
    version: 1.0.1
  express:
    version: 4.18.2
  express-generator:
    version: 4.16.1
  express-validator:
    version: 7.0.1
  fs-extra:
    version: 11.1.1
  generic-pool:
    version: 3.9.0
  helmet:
    version: 6.1.5
  jest:
    version: 29.5.0
  jsonwebtoken:
    version: 9.0.0
  mongodb:
    version: 5.3.0
  npm:
    version: 9.6.5
  pg:
    version: 8.10.0
  pg-hstore:
    version: 2.3.4
  pm2:
    version: 5.3.0
  redis:
    version: 4.6.5
  request:
    version: 2.88.2
  sequelize:
    version: 6.31.0
  sequelize-cli:
    version: 6.6.0
  supervisor:
    last_entry: True
    version: 0.12.0
