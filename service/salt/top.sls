base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}

services:
  '*':
    {% for service in grains.get('services') %}
    - {{ service }}
    {% endfor %}
