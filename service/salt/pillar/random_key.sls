{%- set random_string_generator="echo $'import random\nimport string' | python" -%}

random_key: 
  django_secret_key: {{ salt['cmd.run'](random_string_generator) }}
  frontend_db_key: {{ salt['cmd.run'](random_string_generator) }}
