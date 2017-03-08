{%- set random_string_generator='echo "import random" | python3' -%}

random_key: 
  django_secret_key: {{ salt['cmd.run'](random_string_generator) }}
  frontend_db_key: {{ salt['cmd.run'](random_string_generator) }}
