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
    - server/{{ grains.get('server') }}
    {% endif %}
    {% if grains.get('services') %}
    {% for service in grains.get('services') %}
    - services/{{ service }}
    {% endfor %}
    {% endif %}
    #{% if pillar.stage is defined %}
    #{% for service in pillar[grains.get('stage')]['services'] %}
    #- stage/{{ grains.get('stage') }}/services/{{ service }}
    #{% endfor %}
    #{% elif grains.get('stage') %}
    {% if grains.get('stage') %}
    - stage/develop/services/frontend
    {% endif %}
    #{% for service in pillar[grains.get('stage')]['services'] %}
    #- stage/{{ grains.get('stage') }}/services/{{ service }}
    #{% endfor %}
    #{% endif %}
