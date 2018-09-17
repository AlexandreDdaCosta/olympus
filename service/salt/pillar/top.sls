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
  'server:(unified|backend)':
    - match: grain_pcre
    - services.backend
  'server:(unified|frontend)':
    - match: grain_pcre
    - services.frontend
