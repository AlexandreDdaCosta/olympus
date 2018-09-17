backend-user: node
# Temporary until we start tagging releases
backend-version: 0.1

backend-packages:
  mongodb-org:
    repo: jessie/mongodb-org
  nodejs:
    version: 6.14.4-1nodesource1
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

