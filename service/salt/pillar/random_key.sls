{%- set random_string_generator='echo -e "import random\nimport string\nprint \'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(30))" | python' -%}

random_key: 
  django_secret_key: {{ salt['cmd.run'](random_string_generator) }}
  frontend_db_key: {{ salt['cmd.run'](random_string_generator) }}
