{%- set check_BCM57=salt['cmd.shell']('lspci | egrep -i \'network|ethernet\' | grep Broadcom | grep BCM57 | wc -l') -%}

firmware:
{% if check_BCM57 != '0' %}
  firmware-bnx2:
    version: 20210315-3
{% endif %}
