{% set ploutos_user='ploutos' %}
{% set ploutos_app_path=pillar.apps_path+'/ploutos' %}

include:
  - base: apps
  - base: services.bigdata

{{ ploutos_user }}:
  group:
    - name: {{ ploutos_user }}
    - present
  user:
    - createhome: True
    - fullname: {{ ploutos_user }}
    - home: /home/{{ ploutos_user }}
    - name: {{ ploutos_user }}
    - present
    - shell: /bin/false
    - groups:
      - {{ ploutos_user }}

/home/{{ ploutos_user }}/Downloads:
  file.directory:
    - group: {{ ploutos_user }}
    - makedirs: False
    - mode: 0755
    - user: {{ ploutos_user }}

{{ ploutos_app_path }}:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: {{ ploutos_user }}
    - source: salt://apps/ploutos
    - require:
      - sls: apps
    - user: {{ ploutos_user }}
  cmd.run:
    - name: 'chmod -R 0755 {{ ploutos_app_path }}/scripts'

initialize_ploutos:
  cmd.run:
    - name: "su -s /bin/bash -c '/srv/apps/ploutos/scripts/init.py --graceful' {{ ploutos_user }}"
