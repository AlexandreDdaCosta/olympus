{% for package in pillar['core-packages'] %}
{{ package }}:
  pkg.installed:
    - pkg_verify: True
{% endfor %}
