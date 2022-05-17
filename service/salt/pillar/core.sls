{% set systemname = 'olympus' %}
core-user: root
core-app-user: {{ systemname }}
core-email: alex_investor@yahoo.com
core-staff-user: alex
system-name: {{ systemname }}

core-domain-C: US
core-domain-ST: Florida
core-domain-L: Lake Worth
core-domain-O: LaikasDen
core-domain-OU: Olympus web services
core-domain-CN: laikasden.com

core-states:
  - grains
  - repository
  - package
  - firewall
  - services
  - users
  - security

{# For local router #}
network_ssid: {{ systemname }}

{% set core_server_name = 'zeus' %}
servers:
  database:
    name: apollo
    lan_ip: 192.168.1.178
  interface:
    apps:
      - larry
    lan_ip: 192.168.1.177
    name: hermes
    services:
      - frontend
  supervisor:
    name: {{ core_server_name }}
    lan_ip: 192.168.1.179
    services:
      - backend
  unified:
    apps:
      - larry
    lan_ip: 192.168.1.179
    name: {{ core_server_name }}
    services:
      - backend
      - frontend
  worker:
    names:
      hephaistos:
        lan_ip: 192.168.1.180
      artemis:
        lan_ip: 192.168.1.181
      athena:
        lan_ip: 192.168.1.182
      dionysus:
        lan_ip: 192.168.1.183
      demeter:
        lan_ip: 192.168.1.184
      ares:
        lan_ip: 192.168.1.185
      poseidon:
        lan_ip: 192.168.1.186
      hera:
        lan_ip: 192.168.1.187
      aphrodite:
        lan_ip: 192.168.1.188
    services:
      - bigdata
