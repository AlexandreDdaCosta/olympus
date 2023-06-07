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
    - name: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo_repo_previous'] }}.list

delete_mongodb_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo_repo'] }}.list

{% set mongo_repo_key_name = "/usr/share/keyrings/mongodb-" ~ pillar.mongo_repo ~ ".gpg" %}
mongodb_repo_key:
{% if not salt['file.file_exists' ](mongo_repo_key_name) %}
  cmd.run:
    - name: curl -fsSL https://www.mongodb.org/static/pgp/server-{{ pillar['mongo_repo'] }}.asc | gpg --dearmor -o {{ mongo_repo_key_mname }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ mongo_repo_key_name }}
      - url: https://www.mongodb.org/static/pgp/server-{{ pillar['mongo_repo'] }}.asc
      - is_gpg: False
{% endif %}

mongodb_repo:
  pkgrepo.managed:
    - dist: {{ pillar['previous-release'] }}/mongodb-org/{{ pillar['mongo_repo'] }}
    - file: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo_repo'] }}.list
    - humanname: MongoDB package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb http://repo.mongodb.org/apt/debian {{ pillar['previous-release'] }}/mongodb-org/{{ pillar['mongo_repo'] }} main

delete_nginx_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/nginx.list

{% set nginx_repo_key_name = "/usr/share/keyrings/nginx.gpg" %}
{% if not salt['file.file_exists' ](nginx_repo_key_name) %}
nginx_repo_key:
  cmd.run:
    - name: curl -fsSL http://nginx.org/keys/nginx_signing.key | gpg --dearmor -o {{ nginx_repo_key_name }}
{% endif %}

nginx_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb http://nginx.org/packages/debian/ {{ pillar['release'] }} nginx

nginx_src_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nginx.list
    - humanname: Nginx source repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb-src http://nginx.org/packages/debian/ {{ pillar['release'] }} nginx

delete_nodesource_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/nodesource.list

{% set nodesource_repo_key_name = "/usr/share/keyrings/nodesource.gpg" %}
{% if not salt['file.file_exists' ](nodesource_repo_key_name) %}
node_repo_key:
  cmd.run:
    - name: curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | gpg --dearmor -o {{ nodesource_repo_key_name }}
{% endif %}

nodesource_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nodesource.list
    - humanname: Nodesource node.js package repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb https://deb.nodesource.com/{{ pillar['nodejs-repo'] }} {{ pillar['release'] }} main

nodesource_src_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}
    - file: /etc/apt/sources.list.d/nodesource.list
    - humanname: Nodesource node.js source repository for {{ pillar['distribution'] }} {{ pillar['release'] }}
    - name: deb-src https://deb.nodesource.com/{{ pillar['nodejs-repo'] }} {{ pillar['release'] }} main

delete_postgresql_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/pgdg.list

{% set postgresql_repo_key_name = "/usr/share/keyrings/postgresql.gpg" %}
{% if not salt['file.file_exists' ](postgresql_repo_key_name) %}
postgresql_repo_key:
  cmd.run:
    - name: curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o {{ postgresql_repo_key_name }}
{% endif %}

postgresql_repo:
  pkgrepo.managed:
    - dist: {{ pillar['release'] }}-pgdg
    - file: /etc/apt/sources.list.d/pgdg.list
    - humanname: PostgreSQL repository
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{ pillar['release'] }}-pgdg main

delete_sysdig_repo:
  file.absent:
    - name: /etc/apt/sources.list.d/sysdig.list

{% set sysdig_repo_key_name = "/usr/share/keyrings/sysdig.gpg" %}
{% if not salt['file.file_exists' ](sysdig_repo_key_name) %}
sysdig_repo_key:
  cmd.run:
    - name: curl -fsSL https://s3.amazonaws.com/download.draios.com/DRAIOS-GPG-KEY.public | gpg --dearmor -o {{ sysdig_repo_key_name }}
{% endif %}

sysdig_repo:
  pkgrepo.managed:
    - file: /etc/apt/sources.list.d/sysdig.list
    - humanname: sysdig repository
    - name: deb https://download.sysdig.com/stable/deb stable-$(ARCH)/
