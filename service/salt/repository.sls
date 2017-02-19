nginx_jessie:
  pkgrepo.managed:
    - humanname: Nginx package repository for Debian jessie
    - name: deb http://nginx.org/packages/debian/ jessie nginx
    - dist: jessie
    - file: /etc/apt/sources.list.d/nginx.list

nginx_src_jessie:
  pkgrepo.managed:
    - humanname: Nginx source repository for Debian jessie
    - name: deb-src http://nginx.org/packages/debian/ jessie nginx
    - dist: jessie
    - file: /etc/apt/sources.list.d/nginx.list
