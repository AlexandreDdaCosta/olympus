base:
  '*':
    {% for state in ext_pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
