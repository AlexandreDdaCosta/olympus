olympus.db:
  postgres_database.present:
    - name: olympus

frontend_app_data.db:
  postgres_database.present:
    - name: app_data

frontend_user_data.db:
  postgres_database.present:
    - name: user_data

forntend_app_data.db_user:
  postgres_user.present:
    - encrypted: True
    - name: uwsgi
    - password: 'md5{MD5OF({{ pillar['random_key']['app_data_db_key'] }})}'

forntend_user_data_db_user:
  postgres_user.present:
    - encrypted: True
    - name: uwsgi
    - password: 'md5{MD5OF({{ pillar['random_key']['user_data_db_key'] }})}'
