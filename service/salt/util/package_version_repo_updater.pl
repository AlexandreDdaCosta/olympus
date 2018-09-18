#!/usr/bin/env perl

my $intro = <<'ENDINTRO';
-------------------------------
package_version_repo_updater.pl
-------------------------------

Identifies differences between version numbers of installed packages
and those indicated in salt pillar files from the local git repository. 
Creates updated salt files in /tmp.

This utility is Used for managing package updates.
ENDINTRO
print $intro;
print "Enter (Y/y) to execute: " ;
my $proceed = <STDIN>;
$proceed =~ s/\s//g;
if ($proceed !~ /^(Y|y)$/)
{
    print "Terminating.\n";
    exit 0;
}

use strict;
use Data::Dumper;
use Cwd qw{abs_path getcwd};

use vars qw{@data $installed_packages $results @UPDATES};
my $GIT_FILE_DIR= q{../../salt/pillar/};
my @GIT_FILES= ('services.sls','distribution.sls');
my $outfile_prefix = q{/tmp/package_version_repo_updater.}.time().q{.};

my $abs_dir = abs_path($0);
$abs_dir =~ s/^(.*)(\/)(.*?)$/$1/;
chdir $abs_dir;

print qq{Getting installed package data...\n};
print qq{Reading apt...\n};
$installed_packages->{'apt'} = {};
$results = `apt list --installed 2>&1`;
@data = split "\n", $results;
foreach my $line (@data)
{
    next if ($line !~ /\[.*?installed.*?\]/);
    my @entry = split ' ', $line;
    #print join(", ", @entry) . qq{\n};
    my $package = $entry[0];
    $package =~ s/\/[^\s]*$//;
    $installed_packages->{'apt'}->{$package} = $entry[1];
}
print qq{Reading pip3...\n};
$installed_packages->{'pip3'} = {};
$results = `pip3 list 2>&1`;
@data = split "\n", $results;
foreach my $line (@data)
{
    next if ($line !~ /^[^\s]+ \([^\s]+\)$/);
    my @entry = split ' ', $line;
    #print join(", ", @entry) . qq{\n};
    my $package = lc $entry[0];
    my $version = $entry[1];
    $version =~ s/\(([^\s]*)\)/$1/;
    $installed_packages->{'pip3'}->{$package} = $version;
}
print qq{Reading npm...\n};
$installed_packages->{'npm'} = {};
$results = `npm list -g --depth=0 2>&1`;
@data = split "\n", $results;
foreach my $line (@data)
{
    my @entry = split ' ', $line;
    next if (! defined $entry[1]);
    #print join(", ", @entry) . qq{\n};
    my ($module,$version) = split '@', $entry[1];
    $installed_packages->{'npm'}->{$module} = $version;
}
print qq{Reading gem...\n};
$installed_packages->{'gem'} = {};
$results = `gem query --local 2>&1`;
@data = split "\n", $results;
foreach my $line (@data)
{
    my ($package,$version,$more_versions) = split ' ', $line;
    next if (! defined $version);
    if (defined $more_versions)
    {
        $version =~ s/\,/\)/;
    }
    #print qq{$package $version\n};
    next if ($version !~ /^\([^\s]+\)$/);
    $version =~ s/[\(\)]//g;
    $installed_packages->{'gem'}->{$package} = $version;
}
#print Dumper $installed_packages;

print qq{Examining package versions in salt state files from repository...\n};
foreach my $filename (@GIT_FILES)
{
    print "Reading $filename...\n";
    my $filepath = $GIT_FILE_DIR . $filename;
    (-e $filepath) || die "Can't locate $filename. Pillar file must be in a git repo, along with this script.";
    my $STATE_FILE_UPDATES=0;
    my $NEW_STATE_FILE = '';
    my $installer = undef;
    my $package = undef;
	open(GITFILE,"$filepath") || die "Can't open $filepath";
    while (<GITFILE>)
    {
        chop;
        #print $_.qq{\n};
        if ($_ =~ /^[^\s]*packages\:$/)
        {
            #print "Package stanza $_\n";
            # pip3, npm, gem, <none>
            if ($_ =~ /\-pip3\-/)
            {
                $installer = 'pip3'
            }
            elsif ($_ =~ /\-npm\-/)
            {
                $installer = 'npm'
            }
            elsif ($_ =~ /\-gem\-/)
            {
                $installer = 'gem'
            }
            else
            {
                $installer = 'apt'
            }
            $NEW_STATE_FILE .= $_.qq{\n};
            next;
        }
        elsif ($_ =~ /^\s*?$/)
        {
            # divider or end of stanza
            $installer = undef;
            $package = undef;
        }
        if (defined $installer)
        {
            if (defined $package and $_ !~ /^  [^\s]+/)
            {
                if ($_ =~ /^\s+version\:/)
                {
                    my $version = $_;
                    #print qq{version $version\n};
                    if ($installer ne 'pip3')
                    {
                        $version =~ s/^(\s+version\:\s*)([^\s]*)(\s*?)$/$2/;
                    }
                    else
                    {
                        $version =~ s/^(\s+version\:\s*\=\=\s*)([^\s]*)(\s*?)$/$2/;
                    }
                    #print qq{version2 $version\n};
                    #print qq{Installed version: [} . $installed_packages->{$installer}->{$package} . qq{] SLS version: [$version] [$installer] [$package]\n};
                    if ($version ne $installed_packages->{$installer}->{$package})
                    {
                        if (exists $installed_packages->{$installer}->{$package})
                        {
                            print qq{$installer $package $version ----> $installed_packages->{$installer}->{$package}\n};
                            my $line_to_update = $_;
                            if ($installer eq 'pip3')
                            {
                                $line_to_update =~ s/^(\s+version\:\s*\=\=\s*)([^\s]*)(\s*?)$/$1$installed_packages->{$installer}->{$package}$3/;
                            }
                            else
                            {
                                $line_to_update =~ s/^(\s+version\:\s*).*$/$1$installed_packages->{$installer}->{$package}$3/;
                            }
                            $STATE_FILE_UPDATES++;
                            $NEW_STATE_FILE .= $line_to_update.qq{\n};
                            next;
                        }
                        else
                        {
                            print qq{$installer Specified SLS package $package NOT INSTALLED\n};
                        }
                    }
                }
            }
            elsif ($_ =~ /^  [^\s]+/)
            {
                # package name
                $package = $_;
                $package =~ s/\:$//;
                $package =~ s/\s//g;
                #print qq{package $package\n};
            }
        }
        $NEW_STATE_FILE .= $_.qq{\n};
    }
	close(GITFILE);
    #print $NEW_STATE_FILE;
    if ($STATE_FILE_UPDATES)
    {
        my $outfile = $outfile_prefix . $filename;
        open OUTFILE, ">$outfile" or die "Failed to create output file $outfile";
        print OUTFILE $NEW_STATE_FILE;
        close OUTFILE;
        #print qq{Outfile for $filename created in $outfile\n};
        push @UPDATES, $outfile;
    }
}

if (@UPDATES)
{
my $end_header = <<'ENDHEADER';

------------------------
Listing of updated files
------------------------
ENDHEADER
    print $end_header;
    foreach my $outfile (@UPDATES)
    {
        my $root_file_name = $outfile;
        $root_file_name =~ s/^(.*\.)(.*?)(\.sls)$/$2$3/;
        print qq{\n$root_file_name:\n};
        system(qq{ls -la $outfile});
    }
}
else
{
    print qq{No required updates detected\n};
}
exit 0
