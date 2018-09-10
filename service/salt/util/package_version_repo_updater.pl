#!/usr/bin/env perl

# Indicates differences between version numbers of installed packages
# and those in the attached git repository. Update version numbers
# in repository on request. Used for managing package updates.

use strict;
use Data::Dumper;
use Cwd qw{abs_path getcwd};

use vars qw{@GIT_FILES $PACKAGE_VERSIONS};
my @GIT_FILES= ('../../salt/pillar/services.sls','../../salt/pillar/distribution.sls');

print abs_path($0)."\n";
my $abs_dir = abs_path($0);
$abs_dir =~ s/^(.*)(\/)(.*?)$/$1/;
chdir $abs_dir;
foreach my $filepath (@GIT_FILES)
{
    my $filename = $filepath;
    $filename =~ s/^(.*)(\/)(.*?)$/$3/;
    print "Finding $filename\n";
    (-e $filepath) || die "Can't locate $filename; is executable in a git repo?";
    $PACKAGE_VERSIONS->{$filename} = {};
	open(GITFILE,"$filepath") || die "Can't open $filepath";
    while (<GITFILE>)
    {
        if ($_ =~ /\-packages\:$/)
        {
            print $_."\n";
        }
    }
	close(GITFILE);
}

