nginx_jessie:
  pkgrepo.managed:
    - dist: jessie
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx package repository for Debian jessie
    - key_url: http://nginx.org/keys/nginx_signing.key
    - name: deb http://nginx.org/packages/debian/ jessie nginx

nginx_src_jessie:
  pkgrepo.managed:
    - dist: jessie
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx source repository for Debian jessie
    - key_url: http://nginx.org/keys/nginx_signing.key
    - name: deb-src http://nginx.org/packages/debian/ jessie nginx
