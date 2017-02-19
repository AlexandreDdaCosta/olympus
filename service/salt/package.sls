packages:
  pkg.installed:
    - pkgs:
      {% for package in pillar['core-packages'] %}
      {% if pillar['initialization'] == true %}
      - {{ package }}
      {% elif package['version'] %}
      - {{ package }}:
        - version: {{ package['version'] }}
      {% else %}
      - {{ package }}
      {% endif %}
      {% endfor %}
