nginx_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - gpgcheck: 1
    - gpgkey: file:///tmp/nginx_signing.key
    - humanname: Nginx package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - key_url: http://nginx.org/keys/nginx_signing.key
    - name: deb http://nginx.org/packages/debian/ {{ pillar['release'] }} nginx

nginx_src_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - gpgcheck: 1
    - gpgkey: file:///tmp/nginx_signing.key
    - humanname: Nginx source repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - key_url: http://nginx.org/keys/nginx_signing.key
    - name: deb-src http://nginx.org/packages/debian/ {{ pillar['release'] }} nginx
