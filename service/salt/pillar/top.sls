base:
  '*':
    - core
    - distribution
    - hardware
    - apps
    - random_key
    - security
    - services
    - stage
    - users
  'server:(unified|backend)':
    - match: grain_pcre
    - services.backend
    - services.backend.datasources
  'server:(unified|frontend)':
    - match: grain_pcre
    - services.frontend
