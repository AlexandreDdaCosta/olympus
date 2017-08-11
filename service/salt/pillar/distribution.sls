distribution: debian
nodejs-repo: node_6.x
release: jessie

olympus-package-path: /usr/local/lib/python3.4/dist-packages/olympus

repo-packages:
  apt-transport-https:
    version: 1.0.9.8.4

packages:
  at:
    version: 3.1.16-1
  build-essential:
    version: 11.7
  curl:
    version: 7.38.0-4+deb8u5
  fail2ban:
    version: 0.8.13-1
  ntp:
    version: 1:4.2.6.p5+dfsg-7+deb8u2
  ntpdate:
    version: 1:4.2.6.p5+dfsg-7+deb8u2
  openssh-client:
    version: 1:6.7p1-5+deb8u3
  openssh-server:
    version: 1:6.7p1-5+deb8u3
  python-pip:
    version: 1.5.6-5
  python3-dev:
    version: 3.4.2-2
  python3-pip:
    version: 1.5.6-5
  sudo:
    version: 1.8.10p3-1+deb8u3
  vim:
    version: 2:7.4.488-7+deb8u3
