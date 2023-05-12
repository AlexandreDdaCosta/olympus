setup-node-dev:
  cmd.run:
    - cwd: {{ pillar.www_path }}/node/restapi
    - name: npm install --include=dev 

{{ pillar.www_path }}/node/restapi/.eslintrc.json:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/backend/files/.eslintrc.json
    - user: root
