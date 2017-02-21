base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server_type') and pillar['server_types'] %}
    - services/web
    - services/narf
    {% endif %}
