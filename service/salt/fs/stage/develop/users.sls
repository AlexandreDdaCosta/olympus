# For those times in development when editing under sudo just makes things easier.

root-vim:
  file.directory:
    - group: root
    - mode: 0750
    - name: /root/.vim
    - user: root

root-vim-bundle:
  file.directory:
    - group: root
    - mode: 0750
    - name: /root/.vim/bundle
    - user: root

root-vimrc:
  file.managed:
    - group: root
    - mode: 0640
    - name: /root/.vimrc
    - user: root
    - source: salt://users/vimrc.jinja
    - template: jinja

{% for vimpackagename, vimpackage in pillar.get('vim-packages', {}).items() %}
root-vim-{{ vimpackagename }}:
{% if salt['file.directory_exists']('/root/.vim/bundle/' + vimpackagename) %}
  cmd.run:
    - cwd: /root/.vim/bundle/{{ vimpackagename }}
{% if 'git-flags' in vimpackage %}
    - name: git pull {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}
{% else %}
    - name: git pull {{ vimpackage['repo'] }}
{% endif %}
{% else %}
  cmd.run:
    - cwd: /root/.vim/bundle
{% if 'git-flags' in vimpackage %}
    - name: git clone {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}
{% else %}
    - name: git clone {{ vimpackage['repo'] }}
{% endif %}
{% endif %}
{% endfor %}
