{% set release_name = 'bullseye' %}
distribution: debian
mongo-repo: 5.1
nodejs-repo: node_16.x
previous-release: buster
release: {{ release_name }}
release-version: 11
{% set python3 = 3.9.0 %}

python3-version: {{ python3 }}
olympus-app-package-path: /usr/local/lib/python{{ python3 }}/dist-packages
olympus-package-path: /usr/local/lib/python{{ python3 }}/dist-packages/olympus
olympus-scripts-path: /usr/local/bin/olympus

repo-packages:
  apt-transport-https:
    version: 1.8.2.2

packages:
  at:
    version: 3.1.23-1
  build-essential:
    version: 12.6
  curl:
    version: 7.64.0-4+deb10u2
  fail2ban:
    version: 0.10.2-2.1
  ntp:
    version: 1:4.2.8p12+dfsg-4
  ntpdate:
    version: 1:4.2.8p12+dfsg-4
  openssh-client:
    version: 1:7.9p1-10+deb10u2
  openssh-server:
    version: 1:7.9p1-10+deb10u2
  python-pip:
    version: 18.1-5
  python3-dev:
    version: 3.7.3-1
  python3-pip:
    version: 18.1-5
  sudo:
    version: 1.8.27-1+deb10u3
  vim:
    version: 2:8.1.0875-5
