packages:
  pkg.latest:
    - pkgs:
      {% for package in pillar['core-packages'] %}
      - {{ package }}
      {% endfor %}
