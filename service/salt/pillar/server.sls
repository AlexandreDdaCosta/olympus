interface:
  services:
    - python-web
    - ui

supervisor:
  services:
    - node.js-web
    - python-web
