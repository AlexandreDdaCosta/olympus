{% for package in pillar['core-packages'] %}
{{ package }}:
  pkg.installed
{% endfor %}
