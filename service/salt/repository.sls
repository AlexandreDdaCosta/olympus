nginx_jessie:
  pkgrepo.managed:
    - humanname: Nginx package repository for Debian jessie
    - name:
      - deb http://nginx.org/packages/debian/ jessie nginx
      - deb-src http://nginx.org/packages/debian/ jessie nginx
    - dist: jessie
    - file: /etc/apt/sources.list.d/nginx.list
