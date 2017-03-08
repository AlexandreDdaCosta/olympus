olympus.db:
  postgres_database.present:
    - name: olympus

frontend_app_data.db:
  postgres_database.present:
    - name: app_data

frontend_user_data.db:
  postgres_database.present:
    - name: user_data
