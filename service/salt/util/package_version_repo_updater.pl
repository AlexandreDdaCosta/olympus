#!/usr/bin/env perl

# Indicates differences between version numbers of installed packages
# and those in the attached git repository. Update version numbers
# in repository on request. Used for managing package updates.

use strict;
use Data::Dumper;
use Cwd qw{abs_path getcwd};

use vars qw{$PACKAGE_VERSIONS};
my $GIT_FILE_DIR= q{../../salt/pillar/};
my @GIT_FILES= ('services.sls','distribution.sls');
my $outfile_prefix = q{/tmp/package_version_repo_updater.}.time().q{.};

my $abs_dir = abs_path($0);
$abs_dir =~ s/^(.*)(\/)(.*?)$/$1/;
chdir $abs_dir;
foreach my $filename (@GIT_FILES)
{
    print "Finding $filename\n";
    my $filepath = $GIT_FILE_DIR . $filename;
    (-e $filepath) || die "Can't locate $filename. Pillar file must be in a git repo, along with this script.";
    $PACKAGE_VERSIONS->{$filename} = {};
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
            if (! exists $PACKAGE_VERSIONS->{$filename}->{$installer})
            {
                $PACKAGE_VERSIONS->{$filename}->{$installer} = {};
            }
            next;
        }
        elsif ($_ =~ /^\s*?$/)
        {
            # divider or end of stanza
            $installer = undef;
            $package = undef;
            next;
        }
        if (defined $installer)
        {
            if (defined $package and $_ !~ /^  [^\s]+/)
            {
                if ($_ =~ /^\s+version\:/)
                {
                    my $version = $_;
                    if ($installer ne 'pip3')
                    {
                        $version =~ s/^(\s+version\:\s*)([^\s]*)(\s*?)$/$2/;
                    }
                    else
                    {
                        $version =~ s/^(\s+version\:\s*\=\=\s*)([^\s]*)(\s*?)$/$2/;
                    }
                    $PACKAGE_VERSIONS->{$filename}->{$installer}->{$package} = $version;
                }
            }
            elsif ($_ =~ /^  [^\s]+/)
            {
                # package name
                $package = $_;
                $package =~ s/\:$//;
                $package =~ s/\s//g;
                print qq{package $package\n};
                next;
            }
        }
    }
	close(GITFILE);
}
print Dumper $PACKAGE_VERSIONS;

# Get apt, pip3, npm, gem installed data

# Output

foreach my $filename (@GIT_FILES)
{
    # create output file

    my $outfile = $outfile_prefix . $filename;
    open OUTFILE, ">$outfile" or die "Failed to create output file $outfile";
    close OUTFILE;
    print qq{Outfile for $filename created in $outfile\n};
    system(qq{ls -la $outfile});
}
exit 0
