base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server_type') %}
    - server/{{ grains.get('server_type') }}
    {% endif %}
    {% if grains.get('services') %}
    {% for service in grains.get('services') %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
