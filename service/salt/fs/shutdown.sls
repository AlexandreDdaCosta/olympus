include:
  - base: services/frontend

shutdown:
  cmd.run:
{% if pillar.reboot is defined and pillar.reboot %}
    - name: /sbin/shutdown --reboot
{% else %}
    - name: /sbin/shutdown --poweroff +3
{% endif %}
    {% if grains.get('server') %}
    {% if 'services' in pillar[grains.get('server')] %}
    {% if 'frontend' in pillar[grains.get('server')]['services'] %}
    - require:
      - sls: services/frontend
    {% endif %}
    {% endif %}
    {% endif %}
