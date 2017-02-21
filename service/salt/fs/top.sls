base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server_type') %}
    {% for service in pillar['server_types'][grains.get('server_type')]['services'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
