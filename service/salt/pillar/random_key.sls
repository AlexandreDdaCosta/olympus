{%- set random_string_generator='echo -e "import random; import string; print ''.join(random.choice(string.ascii_letters + string.digits) for x in range(30))" | 
/usr/bin/python' -%}

random_key: 
  django_secret_key: {{ salt['cmd.run'](random_string_generator|yaml_encode) }}
  frontend_db_key: {{ salt['cmd.run'](random_string_generator|yaml_encode) }}
