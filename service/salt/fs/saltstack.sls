{%- if grains.get('server') %}
{%- if grains.get('server') == 'supervisor' or grains.get('server') == 'unified' %}

salt-master:
  pkg.latest

/etc/salt/master.d/core.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/master.d/core.conf
    - user: root

/etc/salt/master.d/reactor.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/master.d/reactor.conf
    - user: root

salt-master-service:
  service.running:
    - enable: True
    - name: salt-master
    - restart: True
    - watch:
        - file: /etc/salt/master.d/core.conf
        - file: /etc/salt/master.d/reactor.conf
        - pkg: salt-master

{% endif %}
{% endif %}

salt-minion:
  pkg.latest

/etc/salt/minion.d/core.conf
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/minion.d/core.conf
    - user: root

{% if grains.get('server') %}
{% set server_conf_file=grains.get('server') %}
/etc/salt/minion.d/{{ server_conf_file }}.conf
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/minion.d/{{ server_conf_file }}.conf
    - user: root
{% endif %}

salt-minion-service:
  service.running:
    - enable: True
    - name: salt-minion
    - restart: True
    - watch:
        - file: /etc/salt/minion.d/core.conf
{% if grains.get('server') %}
        - file: /etc/salt/minion.d/{{ server_conf_file  }}.conf
{% endif %}
        - pkg: salt-minion
