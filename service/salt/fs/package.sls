include:
  - repository

{% for packagename, package in pillar.get('packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
    {% endif %}
{% endif %}
{% if package != None and 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: repository
{% endfor %}

{% for packagename, package in pillar.get('firmware', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
    {% endif %}
{% endif %}
    - require:
      - sls: repository
{% endfor %}

salt-2018.3.2+ds-1-pip3-bug-hack:
  cmd:
    - run
    - name: perl -e '$file = qq{/usr/lib/python2.7/dist-packages/salt/modules/pip.py}; $res = `apt list --installed 2>\&1 | grep salt-common`; if ($res =~ /2018\.3\.2\+ds\-1/) { open my $in, $file or die "$!"; $/ = undef; my $all = <$in>; close $in; $all =~ s/else (.)python([^3])/else $1python3$2/; open my $out, ">$file" or die "$!"; print $out $all; close $out; }'

{{ pillar['olympus-package-path'] }}:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://core/python3/lib
    - user: root

{{ pillar['olympus-scripts-path'] }}:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://core/bin
    - user: root

{# TEMPORARY REMOVAL for testing
initialize_olympus:
  cmd.run:
    - name: "su -s /bin/bash -c '/usr/local/bin/olympus/init.py --graceful' {{ ploutos_user }}"
    - user: root
#}
