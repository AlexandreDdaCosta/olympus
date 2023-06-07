include:
  - base: grains

{#
I'm leaving this section for now because one supposes that we'll see new 
repository entries using gpg keys in the next major distro.
For that upgrade, this section will need to be revised.
#}
/etc/apt/sources.list:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://repository/sources.list.jinja
    - template: jinja
    - user: root

{% for packagename, package in pillar.get('repo-packages', {}).items() %}
{{ packagename }}-repo-package:
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

delete_mongodb_repo_previous:
  file.absent:
    - name: /etc/apt/sources.list.d/mongodb-org-{{ pillar['mongo_repo_previous'] }}.list

{% set mongo_repo_key_name = "/usr/share/keyrings/mongodb-" ~ pillar.mongo_repo ~ ".gpg" %}
{% set mongo_repo_key_url = "https://www.mongodb.org/static/pgp/server-" ~ pillar.mongo_repo ~ ".asc" %}
mongodb_repository_key:
{% if not salt['file.file_exists' ](mongo_repo_key_name) %}
  cmd.run:
    - name: curl -fsSL {{ mongo_repo_key_url }} | gpg --dearmor -o {{ mongo_repo_key_name }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ mongo_repo_key_name }}
      - url: {{ mongo_repo_key_url }}
      - is_gpg: False
{% endif %}

mongodb_repository_entry:
  module.run:
    - repository.update_repository:
      - name: mongodb-org-{{ pillar['mongo_repo'] }}.sources
      - types:
        - deb
      - architectures: 
        - amd64
      - signed_by: {{ mongo_repo_key_name }}
      - uris: http://repo.mongodb.org/apt/debian
      - suites: 
        - {{ pillar['previous-release'] }}/mongodb-org/{{ pillar['mongo_repo'] }}
      - components:
        - main

{#
{% set nginx_repo_key_name = "/usr/share/keyrings/nginx.gpg" %}
{% set nginx_repo_key_url = "http://nginx.org/keys/nginx_signing.key" %}
{% if not salt['file.file_exists'](nginx_repo_key_name) %}
nginx_repo_key:
  cmd.run:
    - name: curl -fsSL {{ nginx_repo_key_url }} | gpg --dearmor -o {{ nginx_repo_key_name }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ nginx_repo_key_name }}
      - url: {{ nginx_repo_key_url }}
      - is_gpg: False
{% endif %}
#}

{#
nginx_repo:
  module.run:
    - repository.update_repository:
      - name: nginx.sources
      - types:
        - deb
        - deb-src
      - architectures: 
        - amd64
      - signed_by: {{ nginx_repo_key_name }}
      - uris: http://nginx.org/packages/debian/
      - suites: 
        - {{ pillar['release'] }}
      - components:
        - nginx
#}

{#
{% set nodesource_repo_key_name = "/usr/share/keyrings/nodesource.gpg" %}
{% set nodesource_repo_key_url = "https://deb.nodesource.com/gpgkey/nodesource.gpg.key" %}
{% if not salt['file.file_exists'](nodesource_repo_key_name) %}
node_repo_key:
  cmd.run:
    - name: curl -fsSL {{ nodesource_repo_key_url }} | gpg --dearmor -o {{ nodesource_repo_key_name }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ nodesource_repo_key_name }}
      - url: {{ nodesource_repo_key_url }}
      - is_gpg: False
{% endif %}
#}

{#
nodesource_repo:
  module.run:
    - repository.update_repository:
      - name: nodesource.sources
      - types:
        - deb
        - deb-src
      - architectures: 
        - amd64
      - signed_by: {{ nodesource_repo_key_name }}
      - uris: https://deb.nodesource.com/{{ pillar['nodejs-repo'] }}
      - suites: 
        - {{ pillar['release'] }}
      - components:
        - main
#}

{#
{% set postgresql_repo_key_name = "/usr/share/keyrings/postgresql.gpg" %}
{% set postgresql_repo_key_url = "https://www.postgresql.org/media/keys/ACCC4CF8.asc" %}
{% if not salt['file.file_exists'](postgresql_repo_key_name) %}
postgresql_repo_key:
  cmd.run:
    - name: curl -fsSL {{ postgresql_repo_key_url }} | gpg --dearmor -o {{ postgresql_repo_key_name }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ postgresql_repo_key_name }}
      - url: {{ postgresql_repo_key_url }}
      - is_gpg: False
{% endif %}
#}

{#
postgresql_repo:
  module.run:
    - repository.update_repository:
      - name: pgdg.sources
      - types:
        - deb
      - architectures: 
        - amd64
      - signed_by: {{ postgresql_repo_key_name }}
      - uris: http://apt.postgresql.org/pub/repos/apt/
      - suites: 
        - {{ pillar['release'] }}-pgdg
      - components:
        - main
#}

{#
{% set sysdig_repo_key_name = "/usr/share/keyrings/sysdig.gpg" %}
{% set sysdig_repo_key_url = "https://s3.amazonaws.com/download.draios.com/DRAIOS-GPG-KEY.public" %}
{% if not salt['file.file_exists'](sysdig_repo_key_name) %}
sysdig_repo_key:
  cmd.run:
    - name: curl -fsSL {{ sysdig_repo_key_url }} | gpg --dearmor -o {{ sysdig_repo_key_name }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ sysdig_repo_key_name }}
      - url: {{ sysdig_repo_key_url }}
      - is_gpg: False
{% endif %}
#}

{#
sysdig_repo:
  module.run:
    - repository.update_repository:
      - name: sysdig.sources
      - types:
        - deb
      - architectures: 
        - amd64
      - signed_by: {{ sysdig_repo_key_name }}
      - uris: https://download.sysdig.com/stable/deb
      - suites: 
        - {{ pillar['release'] }}
      - components:
        - stable-$(ARCH)/
#}

{#
{% set docker_repo_key_name = "/usr/share/keyrings/docker.gpg" %}
{% set docker_repo_key_url = "https://download.docker.com/linux/debian/gpg" %}
{% if not salt['file.file_exists'](docker_repo_key_name) %}
docker_repo_key:
  cmd.run:
    - name: curl -fsSL {{ docker_repo_key_url }} | gpg --dearmor -o {{ docker_repo_key_name }}
{% else %}
  module.run:
    - repository.update_repository_key:
      - key: {{ docker_repo_key_name }}
      - url: {{ docker_repo_key_url }}
      - is_gpg: False
{% endif %}
#}

{#
docker_repo:
  module.run:
    - repository.update_repository:
      - name: docker.sources
      - types:
        - deb
      - architectures: 
        - amd64
      - signed_by: {{ docker_repo_key_name }}
      - uris: https://download.docker.com/linux/debian
      - suites: 
        - {{ pillar['release'] }}
      - components:
        - stable
#}

update_apt_repositories:
  cmd:
    - run
    - name: 'apt-get update --allow-releaseinfo-change'
