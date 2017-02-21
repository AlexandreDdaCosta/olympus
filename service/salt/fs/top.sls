base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server_type') and pillar['server_types'] %}
    {% for service in pillar['server_types']['supervisor']['services'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
