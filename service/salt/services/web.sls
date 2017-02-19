include:
  - base: repository
  - base: security

web-packages:
  pkg.latest:
    - fromrepo: migrations
    - pkgs:
      - nginx
    - require:
      - sls: repository
