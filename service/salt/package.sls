packages:
  pkg.installed:
    - pkgs:
      {% for package in pillar['core-packages'] %}
      {% if pillar['initialization'] %}
      - {{ package }}
      {% elif package['version'] %}
      - {{ package }}
      {% else %}
      - {{ package }}
      {% endif %}
      {% endfor %}
