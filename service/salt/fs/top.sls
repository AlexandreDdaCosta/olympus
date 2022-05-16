base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if 'services' in pillar['servers'][grains.get('server')] %}
    {% for service in pillar['servers'][grains.get('server')]['services'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
    {% if grains.get('services') %}
    {% for service in grains.get('services') %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
    {% if 'apps' in pillar['servers'][grains.get('server')] %}
    - apps
    {% endif %}
    {% if grains.get('stage') %}
    {% for service in pillar[grains.get('stage')]['services'] %}
    - stage/{{ grains.get('stage') }}/services/{{ service }}
    {% endfor %}
    {% endif %}
