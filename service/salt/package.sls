{% for package in pillar['core-packages'] %}
{{ package }}
  pkg.installed:
    - version: {{ package['version'] }}
{% endfor %}
