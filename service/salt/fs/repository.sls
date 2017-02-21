nginx_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb http://nginx.org/packages/debian/ {{ pillar['release'] }} nginx
  cmd:
    - run
    - name: 'wget -O - http://nginx.org/keys/nginx_signing.key | apt-key add -'
    - unless: 'apt-key list | grep -i nginx' 

nginx_src_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx source repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb-src http://nginx.org/packages/debian/ {{ pillar['release'] }} nginx

jessie_backports_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/jessie-backports.list
    - humanname: Added packages for Debian
    - name: deb http://ftp.debian.org/debian jessie-backports main
