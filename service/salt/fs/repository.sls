include:
  - base: grains

/etc/apt/sources.list:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://repository/sources.list.jinja
    - template: jinja
    - user: root

{% for packagename, package in pillar.get('repo-packages', {}).items() %}
{{ packagename }}-repo:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - name: {{ packagename }}
{% endfor %}

delete_old_backports_file:
  file.absent:
    - name: /etc/apt/sources.list.d/{{ pillar['previous-release'] }}-backports.list:

{{ pillar['release'] }}_backports_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}-backports
    - file: /etc/apt/sources.list.d/{{ pillar['release'] }}-backports.list
    - humanname: Added packages for Debian
    - name: deb http://ftp.debian.org/debian {{ pillar['release'] }}-backports main
  cmd:
    - run
    - name: 'apt-get update'

mongodb_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}/mongodb-org/{{ pillar['mongo-repo'] }}
    - file: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo-repo'] }}.list
    - humanname: MongoDB package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb http://repo.mongodb.org/apt/debian {{ pillar['release'] }}/mongodb-org/{{ pillar['mongo-repo'] }} main
  cmd:
    - run
    - name: 'wget -O - https://www.mongodb.org/static/pgp/server-{{ pillar['mongo-repo'] }}.asc | apt-key add -'
    - unless: 'apt-key list | grep -i MongoDB | grep {{ pillar['mongo-repo'] }}' 

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

nodesource_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nodesource.list
    - humanname: Nodesource node.js package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb https://deb.nodesource.com/{{ pillar['nodejs-repo'] }} {{ pillar['release'] }} main
  cmd:
    - run
    - name: 'wget -qO - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -'
    - unless: 'apt-key list | grep -i nodesource' 

nodesource_src_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nodesource.list
    - humanname: Nodesource node.js source repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb-src https://deb.nodesource.com/{{ pillar['nodejs-repo'] }} {{ pillar['release'] }} main

postgresql_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}-pgdg
    - file: /etc/apt/sources.list.d/pgdg.list
    - humanname: PostgreSQL repository
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{ pillar['release'] }}-pgdg main
  cmd:
    - run
    - name: 'wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -'
    - unless: 'apt-key list | grep -i postgresql'

/usr/local/bin/update_repo_keys.sh:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://repository/files/update_repo_keys.sh
    - user: root

verify_gnupg_keys:
  cmd.run:
    - name: /usr/local/bin/update_repo_keys.sh
