{% set services = pillar[grains['server']]['services'] %}

services:
  grains.list_present:
    - value:
{% for service in services %}
      - {{ service }}
{% endfor %}

