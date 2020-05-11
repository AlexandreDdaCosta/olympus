{% set release-name = 'buster' %}
distribution: debian
mongo-repo: 4.2
nodejs-repo: node_14.x
previous-release: stretch
release: {{ release-name }}
release-version: 10
{% set python3 = 3.8 %}

python3-version: {{ python3 }}
olympus-app-package-path: /usr/local/lib/python{{ python3 }}/dist-packages
olympus-package-path: /usr/local/lib/python{{ python3 }}/dist-packages/olympus
olympus-scripts-path: /usr/local/bin/olympus

repo-packages:
  apt-transport-https:
    version: 1.4.9

packages:
  at:
    version: 3.1.20-3
  build-essential:
    version: 12.3
  curl:
    version: 7.52.1-5+deb9u10
  fail2ban:
    version: 0.9.6-2
  ntp:
    version: 1:4.2.8p10+dfsg-3+deb9u2
  ntpdate:
    version: 1:4.2.8p10+dfsg-3+deb9u2
  openssh-client:
    version: 1:7.4p1-10+deb9u7
  openssh-server:
    version: 1:7.4p1-10+deb9u7
  python-pip:
    version: 9.0.1-2+deb9u1
  python3-dev:
    version: 3.5.3-1
  python3-pip:
    version: 9.0.1-2+deb9u1
  sudo:
    version: 1.8.19p1-2.1+deb9u2
  vim:
    version: 2:8.0.0197-4+deb9u3
