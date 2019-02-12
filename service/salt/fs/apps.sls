include:
  - base: services.bigdata

{% for packagename, package in pillar.get('apps-pip3-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif package != None and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - name: {{ packagename }} {{ package['version'] }}
    {% else %}
    - name: {{ packagename }}
    {% endif %}
{% else %}
    - name: {{ packagename }}
{% endif %}
    - bin_env: '/usr/bin/pip3'
{% endfor %}

{% for app in pillar[grains.get('apps')] %}
app_user_{{ app }}:
  group:
    - name: {{ app }}
    - present
  user:
    - createhome: True
    - fullname: {{ app }}
    - home: /home/{{ app }}
    - name: {{ app }}
    - present
    - shell: /bin/false
    - groups:
      - {{ app }}

/home/{{ app }}/Downloads:
  file.directory:
    - group: {{ app }}
    - makedirs: False
    - mode: 0750
    - user: {{ app }}

/home/{{ app }}/app:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: {{ app }}
    - require:
      - sls: services.bigdata
    - source: salt://apps/{{ app }}
    - user: {{ app }}
  cmd.run:
    - name: 'if [ -d "/home/{{ app }}/app/scripts" ]; then chmod -R 0750 /home/{{ app }}/app/scripts; fi''

{% endfor %}
