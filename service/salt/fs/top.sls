base:
  '*':
    {% for state in pillar['core-states'] %}
    - {{ state }}
    {% endfor %}
    {% if grains.get('server') %}
    {% if 'services' in pillar[grains.get('server')] %}
    {% for service in pillar[grains.get('server')]['services'] %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
    {% endif %}
    {% if grains.get('services') %}
    {% for service in grains.get('services') %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
    {% if grains.get('apps') %}
    {% for app in grains.get('apps') %}
    - apps/{{ app }}
    {% endfor %}
    {% endif %}
    {% if grains.get('stage') %}
    {% for service in pillar[grains.get('stage')]['services'] %}
    - stage/{{ grains.get('stage') }}/services/{{ service }}
    {% endfor %}
    {% endif %}
