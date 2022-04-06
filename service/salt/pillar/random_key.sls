{%- set random_string_generator='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(0,30)))" | /usr/bin/python3' -%}

random_key: 
  ca_key: {{ salt['cmd.shell'](random_string_generator) }}
  django_secret_key: {{ salt['cmd.shell'](random_string_generator) }}
  frontend_db_key: {{ salt['cmd.shell'](random_string_generator) }}
