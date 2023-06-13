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
    - name: iptables-restore -n {{ path }}

web-firewall-restart:
  cmd.run:
    - name: service nginx status; if [ $? = 0 ]; then service nginx restart; fi;
    - require:
      - firewall
