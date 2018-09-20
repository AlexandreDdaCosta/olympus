{%- set check_BCM57=salt['cmd.shell']('lspci | egrep -i \'network|ethernet\' | grep Broadcom | grep BCM57 | wc -l') -%}

firmware:
  firmware-misc-nonfree:
    version: 20161130-3
{% if {{ check_BCM57 }} != '0' %}
  firmware-bnx2:
    version: 20161130-3
{% endif %}
