base:
  '*':
    - core
    - distribution
    - hardware
    - apps
    - random_key
    - security
    - server
    - services
    - stage
    - users
  'server:(unified|backend)':
    - match: grain_pcre
    - services.backend
    - services.backend.credentials
  'server:(unified|frontend)':
    - match: grain_pcre
    - services.frontend
