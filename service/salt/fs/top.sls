base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server') %}
    {% if 'services' in pillar[grains.get('server')] %}
    {% for service in pillar[grains.get('server')]['services'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
    - server/{{ grains.get('server') }}
    {% endif %}
    {% if grains.get('services') %}
    {% for service in grains.get('services') %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
