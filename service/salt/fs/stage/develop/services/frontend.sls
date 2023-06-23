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
    - group: {{ pillar['frontend_user'] }}
    - mode: 0755
    - user: {{ pillar['frontend_user'] }}

{{ pillar['bin_path_scripts'] }}/{{ pillar['dev_start_script'] }}:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/{{ pillar['dev_start_script'] }}
    - user: root

{{ pillar['bin_path_scripts'] }}/{{ pillar['dev_kill_script'] }}:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/{{ pillar['dev_kill_script'] }}
    - user: root

{{ pillar['system_init_scripts_directory'] }}/django-devserver:
  file.managed:
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
      - file: {{ pillar['system_init_scripts_directory'] }}/django-devserver
      - file: {{ pillar.frontend_nginx_conf_file_name }}

{% endif %}
{% endif %}
