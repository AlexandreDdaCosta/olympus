{# Sanity checks for inattentive administrators #}
{% if grains.get('stage') and grains.get('stage') == 'develop' %}
{% if grains.get('server') == 'supervisor' or grains.get('server') == 'unified' %}

setup-node-backend-dev:
  cmd.run:
    - cwd: {{ pillar.www_path }}/node/restapi
    - name: npm install --include=dev 

{{ pillar.www_path }}/node/restapi/.eslintrc.json:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/files/.eslintrc.json
    - user: root

{% endif %}
{% endif %}
