{% set services = pillar[grains['server']]['services'] %}

# Add pillar definitions for services in each server type
reset-services-grains:
  grains.absent:
    - name: services

services:
  grains.list_present:
    - value:
{% for service in services %}
      - {{ service }}
{% endfor %}

