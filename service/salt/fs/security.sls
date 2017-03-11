include:
  - base: package

/etc/ssl/localcerts:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root

openssh-server-service:
  file.managed:
    - group: root
    - mode: 0600
    - name: /etc/ssh/sshd_config
    - source: salt://security/files/sshd_config
    - user: root
    - require:
      - pkg: openssh-server
  service.running:
    - enable: True
    - name: sshd
    - restart: True
    - watch:
        - file: /etc/ssh/sshd_config
        - pkg: openssh-server

fail2ban-service:
  service.running:
    - enable: True
    - name: fail2ban
    - restart: True
    - watch:
        - pkg: fail2ban

sudo-config:
  file.managed:
    - group: root
    - mode: 0440
    - name: /etc/sudoers.d/olympus
    - source: salt://security/files/sudoers.d/olympus
    - user: root

selinux.config:
  file.managed:
    - group: root
    - mode: 0644
    - name: /etc/selinux/config
    - source: salt://security/files/selinux/config
    - user: root

selinux.disable:
  cmd.run:
    - name: echo 0 >/selinux/enforce

90-nproc.conf:
  file.managed:
    - group: root
    - mode: 0644
    - name: /etc/security/limits.d/90-nproc.conf
    - source: salt://security/files/90-nproc.conf
    - user: root

#random_root_password:
#  cmd.run:
#    - name: umask 0077; openssl rand -base64 21 > /root/passwd; cat /root/passwd | passwd root --stdin; rm -f /root/passwd
