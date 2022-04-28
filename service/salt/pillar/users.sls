groups:
  - clientcert
  - servercert

{#
Groups:
  clientcert: Add this group to give a user access to client certificate and key
  servercert: Add this group to give a user access to server certificate and key
#}

users:
  alex:
    comment: Big daddy's account
    createhome: True
    email_address: alex_investor@yahoo.com
    fullname: Alexandre da Costa
    groups:
      - clientcert
      - servercert
    is_staff: True
    ssh_public_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCyJxmQB0fZvrPSGL7mWIuHtIvZNTOGgSaVGaZfYelIffONRB7xQuhCK1pfPQJLgFyeQfAjhxyDmJcrPoQvmC1c9MI0Nz4sMyu318EFGlGBGDi2NgVs7WASriPPoSaDtSu16zaFj6URbi4vu/+qoggkgAsTchvTjnfHh4ftjB9S6+e5c9nVS49oemQnhNMenAL77PpL4oe144kuhJntMfgT8BWgFf3WJ1L+4qMz8TODP4lfw0tXTgwdFy5z6qA1FxrYsf87zgEXxOzeShJl6z0HUW01p+m7Pluepga1QZGybwCwGJOC/wo4w0GRPJUwNMna2l/s5V8uLAdSDwFTE+Z/ alex@zeus
    vimuser: True
  mongodb:
    fullname: MongoDB administrator and run user
    groups:
      - servercert
    server:
      - interface
      - supervisor
      - unified
      - worker
    shell: /usr/sbin/nologin
  node:
    createhome: True
    fullname: Backend API run user
    groups:
      - clientcert
    server:
      - supervisor
      - unified
    shell: /bin/false
  olympus:
    createhome: True
    fullname: Olympus system run user
    groups:
      - clientcert
    shell: /bin/false
  postgres:
    fullname: PostgreSQL administrator
    groups:
      - servercert
    server:
      - supervisor
      - unified
