interface:
  services:
    - python-web
    - ui

supervisor:
  services:
    - nodejs-web
    - python-web
