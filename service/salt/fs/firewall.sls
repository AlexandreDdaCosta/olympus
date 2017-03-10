{% set path='/etc/iptables.up.rules' %}

firewall:
  file.managed:
    - group: root
    - mode: 755
    - name: {{ path }}
    - source: salt://firewall/iptables.up.rules.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: iptables-restore < {{ path }}
