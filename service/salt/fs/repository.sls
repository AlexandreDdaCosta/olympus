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
    - name: /etc/apt/sources.list.d/{{ pillar['previous-release'] }}-backports.list

/etc/apt/sources.list.d/{{ pillar['release'] }}-backports.list:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://repository/backports.list.jinja
    - template: jinja
    - user: root
  cmd:
    - run
    - name: 'apt-get update --allow-releaseinfo-change'

{# WARNING: apt-key is deprecated, so the following MUST be updated before upgrading beyond Debian bullseye #}
{# See https://docs.saltproject.io/en/latest/ref/states/all/salt.states.pkgrepo.html #}
{# See also https://www.digitalocean.com/community/tutorials/how-to-handle-apt-key-and-add-apt-repository-deprecation-using-gpg-to-add-external-repositories-on-ubuntu-22-04 #}

delete_mongodb_repo_previous:
  file.absent:
    - name: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo-repo-previous'] }}.list

delete_mongodb_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo-repo'] }}.list

mongodb_repo:
  pkgrepo.managed:
    - dist: {{ pillar['previous-release'] }}/mongodb-org/{{ pillar['mongo-repo'] }}
    - file: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo-repo'] }}.list
    - humanname: MongoDB package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb http://repo.mongodb.org/apt/debian {{ pillar['previous-release'] }}/mongodb-org/{{ pillar['mongo-repo'] }} main
  cmd:
    - run
    - name: 'wget -O - https://www.mongodb.org/static/pgp/server-{{ pillar['mongo-repo'] }}.asc | apt-key add -'
    - unless: 'apt-key list | grep -i MongoDB | grep {{ pillar['mongo-repo'] }}' 

delete_nginx_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/nginx.list

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

delete_nodesource_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/nodesource.list

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

delete_postgresql_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/pgdg.list

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

delete_pgadmin4_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/pgadmin4.list

pgadmin_repo:
  pkgrepo.managed:
    - file: /etc/apt/sources.list.d/pgadmin4.list
    - humanname: pgAdmin repository
    - name: deb https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/{{ pillar['release'] }} pgadmin4 main
  cmd:
    - run
    - name: 'wget -qO - https://www.pgadmin.org/static/packages_pgadmin_org.pub | apt-key add -'
    - unless: 'apt-key list | grep -i pgadmin'

delete_sysdig_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/sysdig.list

sysdig_repo:
  pkgrepo.managed:
    - file: /etc/apt/sources.list.d/sysdig.list
    - humanname: sysdig repository
    - name: deb https://download.sysdig.com/stable/deb stable-$(ARCH)/
  cmd:
    - run
    - name: 'wget -qO - https://s3.amazonaws.com/download.draios.com/DRAIOS-GPG-KEY.public | apt-key add -'
    - unless: 'apt-key list | grep -i Draios'

{# SaltStack repository keys are added during server initialization and are therefore not managed here. #}

/usr/local/bin/update_repo_keys.sh:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://repository/files/update_repo_keys.sh
    - user: root

verify_gnupg_keys:
  cmd.run:
    - name: /usr/local/bin/update_repo_keys.sh
