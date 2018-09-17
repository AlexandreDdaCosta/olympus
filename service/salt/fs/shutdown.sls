include:
  - base: services/frontend

{% if grains.get('server') == 'supervisor' or grains.get('server') == 'unified' %}
{% if pillar.nobackup is not defined or not pillar.nobackup %}
shutdown_backup:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' backup.usb_backup_olympus
{% endif %}
{% endif %}

shutdown:
  cmd.run:
{% if pillar.reboot is defined and pillar.reboot %}
    - name: /sbin/shutdown --reboot
{% else %}
    - name: /sbin/shutdown --poweroff +3
{% endif %}
    {% if grains.get('server') %}
    {% if 'services' in pillar[grains.get('server')] %}
    {% if 'frontend' in pillar[grains.get('server')]['services'] %}
    - require:
      - sls: services/frontend
    {% endif %}
    {% endif %}
    {% endif %}
