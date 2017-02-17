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

stage:
  '*':
    {% if grains.get('stage') == 'develop' %}
    - develop.builder
    {% endif %}
    - dist
