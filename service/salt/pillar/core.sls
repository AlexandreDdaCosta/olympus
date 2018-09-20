{% set systemname = 'olympus' %}
core-user: root
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
  - security
  - firewall
  - services
  - users

{# For local router; LAN settings #}
{% set core_lan_ip = '192.168.1.179' %}
network_ssid: {{ systemname }}
interface_lan_ip: {{ core_lan_ip }}
supervisor_lan_ip: 192.168.1.178
unified_lan_ip: {{ core_lan_ip }}

{% set core_server_name = 'zeus' %}
interface_name: apollo
supervisor_name: {{ core_server_name }}
unified_master_name: {{ core_server_name }}

