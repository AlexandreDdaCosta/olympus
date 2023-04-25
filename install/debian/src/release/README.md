# Installation source files

Within these directories, source files for different Debian releases
are organized.

Follow these steps on a network-accessible machine to create a preselected
archive used to install olympus on a machine without network connectivity.

* Install development tools

```
apt-get install dpkg-dev
```

Per the Debian package archives: *This package provides the development
tools (including dpkg-source) required to unpack, build and upload Debian
source packages.*

* Download each required package

```
* apt-get install --download-only <package>
```

Downloads get written to "/var/cache/apt/archives".

* Collect all ".deb" files into a temporary directory.

* Change into temporary directory and create the archive

```
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
```

* If desired, move directory to its final location

* Add source as new file "/etc/apt/sources.list.d/apt-local:

```
deb file:<path_to_directory> ./
```

