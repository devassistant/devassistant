#!/bin/bash
# This script creates an RPM from a tar file.
# $1 : tar file

NAME=$(echo ${1%%-*} | sed 's/^.*\///')
VERSION=$(echo ${1##*-} | sed 's/[^0-9]*$//')
RELEASE=0
SUMMARY="C Language example delivered by Development Assistant Tool"
LICENSE="BSD and GPLv3+ and GPLv2+ and GPLv2"
GROUP="Applications"
DESCRIPTION="This is sample spec file created on the base of c binary packages
It is a part of Development Assistant Tool
"

######################################################
# users should not change the script below this line.#
######################################################

# This function prints the usage help and exits the program.
usage(){
    /bin/cat << USAGE

This script has been released under BSD license. Copyright (C) 2010 Reiner Rottmann <rei..rATrottmann.it>

$0 creates a simple RPM spec file from the contents of a tarball. The output may be used as starting point to create more complex RPM spec files.
The contents of the tarball should reflect the final directory structure where you want your files to be deployed. As the name and version get parsed
from the tarball filename, it has to follow the naming convention "<name>-<ver.si.on>.tar.gz". The name may only contain characters from the range
[A-Z] and [a-z]. The version string may only include numbers seperated by dots.

Usage: $0  [TARBALL]

Example:
  $ $0 sample-1.0.0.tar.gz
  
  $ /usr/bin/rpmbuild -ba /tmp/sample-1.0.0.spec 

USAGE
    exit 1    
}

if echo "${1##*/}" | sed 's/[^0-9]*$//' | /bin/grep -q  '^[a-zA-Z]\+-[0-9.]\+$'; then
   if /usr/bin/file -ib "$1" | /bin/grep -q "application/x-gzip"; then
      echo "INFO: Valid input file '$1' detected."
   else
      usage
   fi
else
    usage
fi

OUTPUT=/tmp/${NAME}.spec

/bin/cat > $OUTPUT << EOF
Name: $NAME
Version: $VERSION
Release: $RELEASE
Summary: $SUMMARY
License: $LICENSE
Group: $GROUP
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: libtool
Requires: gcc

%description
$DESCRIPTION

%prep
%setup -q -n %{name}-%{version}

%build
%configure 
make %{?_smp_mflags}

%install
rm -rf \${RPM_BUILD_ROOT}
make install DESTDIR=\$RPM_BUILD_ROOT

install -p -m 755 -D src/client \${RPM_BUILD_ROOT}%{_bindir}/client
install -p -m 755 -D src/server \${RPM_BUILD_ROOT}%{_bindir}/server
install -p -m 755 -D src/fileOperations \${RPM_BUILD_ROOT}%{_bindir}/fileOperations
install -p -m 755 -D src/simpleThread \${RPM_BUILD_ROOT}%{_bindir}/simpleThread
%post

%postun

%check
make check

%clean
rm -rf \${RPM_BUILD_ROOT}

%files
%defattr(-,root,root)
%{_bindir}/client
%{_bindir}/fileOperations
%{_bindir}/server
%{_bindir}/simpleThread

%define date    %(echo \`LC_ALL="C" date +"%a %b %d %Y"\`)

%changelog

* %{date} User $EMAIL
- first Version

EOF

echo "INFO: Spec file has been saved as '$OUTPUT':"
echo "----------%<----------------------------------------------------------------------"
/bin/cat $OUTPUT
echo "----------%<----------------------------------------------------------------------"
