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
  cmd.run:
    - sudo -u postgres psql -c "ALTER USER uwsgi ENCRYPTED PASSWORD '{{ pillar['random_key']['frontend_db_key'] }}';"

frontend_app_data_privs:
  postgres_privileges.present:
    - name: uwsgi
    - object_name: app_data
    - object_type: database
    - privileges:
      - DELETE
      - EXEC
      - INSERT
      - SELECT

frontend_user_data_privs:
  postgres_privileges.present:
    - name: uwsgi
    - object_name: user_data
    - object_type: database
    - privileges:
      - DELETE
      - EXEC
      - INSERT
      - SELECT

frontend_app_data_privs:
  postgres_privileges.present:
    - name: uwsgi
    - object_name: app_data
    - object_type: database
    - privileges:
      - DELETE
      - EXEC
      - INSERT
      - SELECT
