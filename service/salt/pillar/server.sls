interface:
  services:
    - frontend

supervisor:
  services:
    - backend

unified:
  services:
    - backend
    - frontend

worker:
  services:
    - bigdata

{% set local_services = pillar[grains['server']]['services'] }}
services:
{% for service in local_services %}
  - {{ service }}
{% endfor %}
