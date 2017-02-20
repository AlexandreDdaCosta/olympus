base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}

{% if grains.get('services') %}
services:
  '*':
    {% for service in grains.get('services') %}
    - {{ service }}
    {% endfor %}
{% endif %}
