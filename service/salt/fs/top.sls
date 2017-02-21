base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('services') %}
    {% for service in pillari['supervisor'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
