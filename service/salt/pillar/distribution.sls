{% set release_name = 'bullseye' %}
distribution: debian
mongo-repo: 5.0
mongo-repo-previous: 4.4
nodejs-repo: node_16.x
previous-release: buster
release: {{ release_name }}
release-version: 11
{% set python3 = 3.7 %}

python3-version: {{ python3 }}
olympus-app-package-path: /usr/local/lib/python{{ python3 }}/dist-packages
olympus-package-path: /usr/local/lib/python{{ python3 }}/dist-packages/olympus
olympus-scripts-path: /usr/local/bin/olympus

repo-packages:
  apt-transport-https:
    version: 2.2.4

packages:
  at:
    version: 3.1.23-1.1
  build-essential:
    version: 12.9
  curl:
    version: 7.74.0-1.3+deb11u1
  fail2ban:
    version: 0.11.2-2
  ntp:
    version: 1:4.2.8p15+dfsg-1
  ntpdate:
    version: 1:4.2.8p15+dfsg-1
  openssh-client:
    version: 1:8.4p1-5
  openssh-server:
    version: 1:8.4p1-5
  python-pip:
    version: 18.1-5
  python3-dev:
    version: 3.9.2-3
  python3-pip:
    version: 20.3.4-4+deb11u1
  sudo:
    version: 1.9.5p2-3
  vim:
    version: 2:8.2.2434-3+deb11u1
