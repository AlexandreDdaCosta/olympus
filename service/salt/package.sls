{% for package in pillar['core-packages'] %}
{{ package }}:
  pkg.installed:
    - version: 2:7.4.488-7+deb8u2
{% endfor %}
