    #{% if pillar.stage is defined %}
    #{% for service in pillar[grains.get('stage')]['services'] %}
    #- stage/{{ grains.get('stage') }}/services/{{ service }}
    #{% endfor %}
    #{% elif grains.get('stage') %}
    #- stage
    #- stage/develop/services/frontend
    #{% endif %}
    #{% for service in pillar[grains.get('stage')]['services'] %}
    #- stage/{{ grains.get('stage') }}/services/{{ service }}
    #{% endfor %}
    #{% endif %}
