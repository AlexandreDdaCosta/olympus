{%- set random_string_generator='echo -e "print(\"foo\")" | python3' -%}
#{%- set random_string_generator='echo -e "import random\\nimport string\\nprint \'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(30))" | python3' -%}

random_key: 
  app_data_db_key: {{ salt['cmd.run'](random_string_generator) }}
  django_secret_key: {{ salt['cmd.run'](random_string_generator) }}
  user_data_db_key: {{ salt['cmd.run'](random_string_generator) }}
