base:
  '*':
    - core
    - distribution
    - projects
    - random_key
    - security
    - server
    - services
    - stage
    - users
  'server:(unified|frontend)':
    - match: grain_pcre
    - services.frontend
