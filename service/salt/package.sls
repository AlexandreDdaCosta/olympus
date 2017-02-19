packages:
  pkg.installed:
    - pkgs:
      {% for package in pillar['core-packages'] %}
      {% if pillar['initialization'] %}
      - {{ package }}
      {% else %}
      - {{ package }}
      {% endif %}
      {% endfor %}
