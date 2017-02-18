base:
  '*':
    - staff
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
