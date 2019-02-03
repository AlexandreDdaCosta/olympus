{% set release_name = 'stretch' %}
distribution: debian
mongo-repo: 4.0
nodejs-repo: node_10.x
release: {{ release_name }}
release-version: 9
{% set python3 = 3.5 %}

{#

Debian 8 backup

{% set release_name = 'jessie' %}
distribution: debian
mongo-repo: 3.4
nodejs-repo: node_6.x
release: {{ release_name }}
release-version: 8
{% set python3 = 3.4 %}
#}

python3-version: {{ python3 }}
olympus-package-path: /usr/local/lib/python{{ python3 }}/dist-packages/olympus

repo-packages:
  apt-transport-https:
    version: 1.4.9

packages:
  at:
    version: 3.1.20-3
  build-essential:
    version: 12.3
  curl:
    version: 7.52.1-5+deb9u8
  fail2ban:
    version: 0.9.6-2
  ntp:
    version: 1:4.2.8p10+dfsg-3+deb9u2
  ntpdate:
    version: 1:4.2.8p10+dfsg-3+deb9u2
  openssh-client:
    version: 1:7.4p1-10+deb9u4
  openssh-server:
    version: 1:7.4p1-10+deb9u4
  python-pip:
    version: 9.0.1-2
  python3-dev:
    version: 3.5.3-1
  python3-pip:
    version: 9.0.1-2
  sudo:
    version: 1.8.19p1-2.1
  vim:
    version: 2:8.0.0197-4+deb9u1
