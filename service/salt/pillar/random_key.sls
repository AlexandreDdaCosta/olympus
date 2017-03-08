{%- set random_string_generator='echo "import random" | python3' -%}

random_key: 
  app_data_db_key: {{ salt['cmd.run'](random_string_generator) }}
  django_secret_key: {{ salt['cmd.run'](random_string_generator) }}
  user_data_db_key: {{ salt['cmd.run'](random_string_generator) }}
