base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server_type') %}
    {% set server_type=grains.get('server_type') %}
    {% for service in pillar(server_type)] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
