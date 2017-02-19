packages:
  pkg.installed:
    - pkgs:
      {% for package in pillar['core-packages'] %}
      - {{ package }}
      {% endfor %}
