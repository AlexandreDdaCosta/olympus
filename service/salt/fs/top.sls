base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server_type') %}
    {% for service in pillar['supervisor'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
