nginx_repo:
  pkgrepo.managed:
    - dist: {{ pillar['debian_release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx package repository for Debian {{ pillar['debian_release'] }}
    - key_url: http://nginx.org/keys/nginx_signing.key
    - name: deb http://nginx.org/packages/debian/ {{ pillar['debian_release'] }} nginx

nginx_src_repo:
  pkgrepo.managed:
    - dist: {{ pillar['debian_release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx source repository for Debian {{ pillar['debian_release'] }}
    - key_url: http://nginx.org/keys/nginx_signing.key
    - name: deb-src http://nginx.org/packages/debian/ {{ pillar['debian_release'] }} nginx
