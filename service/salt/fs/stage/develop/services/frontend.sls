{% set kill_script_name = 'killserver.sh' -%}
{% set start_script_name = 'startserver.py' -%}

include:
  - base: services/frontend

{# Sanity checks for inattentive administrators #}
{% if grains.get('stage') and grains.get('stage') == 'develop' %}
{% if grains.get('server') == 'interface' or grains.get('server') == 'unified' %}

{# Enable permanent dev server for highstate run by setting "stage" grain. Useful commands:

sudo -i salt '*' grains.setval stage develop
sudo -i salt '*' grains.delval stage

Currently the dev server does not restart automatically on server shutdown, unlike the
full uWSGI server.
#}

{{ pillar['system_logrotate_conf_directory'] }}/devserver:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/frontend/files/logrotate.devserver
    - user: root

{{ pillar['system_log_directory'] }}/devserver:
  file.directory:
    - group: uwsgi
    - mode: 0755
    - user: uwsgi

{{ pillar['bin_path_scripts'] }}/{{ start_script_name }}:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/{{ start_script_name }}
    - user: root

{{ pillar['bin_path_scripts'] }}/{{ kill_script_name }}:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/{{ kill_script_name }}
    - user: root

{{ pillar['system_init_scripts_directory'] }}/django-devserver:
  file.managed:
    - context:
      kill_script_name: {{ kill_script_name }}
      start_script_name: {{ start_script_name }}
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://stage/develop/services/frontend/init.django-devserver.jinja
    - template: jinja
    - user: root

develop-interface.conf:
  file.managed:
    - group: root
    - name: {{ pillar['frontend_nginx_conf_file_name'] }}
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/frontend/interface.conf.jinja
    - template: jinja
    - user: root

web-django-devserver:
  service.running:
    - enable: True
    - name: django-devserver
    - watch:
      - file: {{ system_init_scripts_directory }}/django-devserver
      - file: {{ pillar.frontend_nginx_conf_file_name }}

{% endif %}
{% endif %}
