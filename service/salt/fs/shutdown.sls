include:
  - base: services/frontend

shutdown:
  cmd.run:
    - name: /sbin/shutdown --poweroff +3
    {% if grains.get('server') %}
    {% if 'services' in pillar[grains.get('server')] %}
    {% if 'frontend' in pillar[grains.get('server')]['services'] %}
    - require:
      - sls: services/frontend
    {% endif %}
    {% endif %}
    {% endif %}
