include:
  - base: services/web

nginx:
  service.running:
    - watch:
      - file: /etc/nginx/conf.d/default.conf
  file.managed:
    - name: /etc/nginx/conf.d/default.conf
    - source: salt://server/supervisor/files/default.conf
  require:
    - sls: services/web
