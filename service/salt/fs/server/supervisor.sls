olympus.db:
  postgres_database.present:
    - name: olympus

frontend_app_data.db:
  postgres_database.present:
    - name: app_data

frontend-user_data.db:
  postgres_database.present:
    - name: user_data

frontend_db_user:
  postgres_user.present:
    - encrypted: True
    - name: {{ pillar['frontend-user'] }}
    - password: 'md5{MD5OF({{ pillar['random_key']['frontend_db_key'] }})}'

frontend_db_user_pwd_reset:
  cmd.run:
    - name: sudo -u postgres psql -c "ALTER USER {{ pillar['frontend-user'] }} ENCRYPTED PASSWORD '{{ pillar['random_key']['frontend_db_key'] }}';"

frontend_app_data_privs:
  postgres_privileges.present:
    - name: {{ pillar['frontend-user'] }}
    - object_name: app_data
    - object_type: database
    - privileges:
      - ALL

frontend-user_data_privs:
  postgres_privileges.present:
    - name: {{ pillar['frontend-user'] }}
    - object_name: user_data
    - object_type: database
    - privileges:
      - ALL
