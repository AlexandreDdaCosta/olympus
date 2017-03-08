olympus.db:
  postgres_database.present:
    - name: olympus

frontend_app_data.db:
  postgres_database.present:
    - name: app_data

frontend_user_data.db:
  postgres_database.present:
    - name: user_data

frontend_db_user:
  postgres_user.present:
    - encrypted: True
    - name: uwsgi
    - password: 'md5{MD5OF({{ pillar['random_key']['frontend_db_key'] }})}'

frontend_db_user_pwd_reset:
  cmd.run:
    - name: sudo -u postgres psql -c "ALTER USER uwsgi ENCRYPTED PASSWORD '{{ pillar['random_key']['frontend_db_key'] }}';"

frontend_app_data_privs:
  postgres_privileges.present:
    - name: uwsgi
    - object_name: app_data
    - object_type: database
    - privileges:
      - CONNECT

frontend_user_data_privs:
  postgres_privileges.present:
    - name: uwsgi
    - object_name: user_data
    - object_type: database
    - privileges:
      - CONNECT

settings.local:
  file.managed:
    - dir_mode: 0755
    - group: uwsgi
    - name: /srv/www/django/interface/settings_local.py
    - makedirs: False
    - mode: 0640
    - source: salt://services/frontend/settings_local.jinja
    - template: jinja
    - user: uwsgi
  require:
    - sls: frontend
