Name: cdevelopmenttool
Version: 0.0
Release: 0
Summary: C Language example delivered by Development Assistant Tool
License: BSD and GPLv3+ and GPLv2+ and GPLv2
Group: Applications
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: libtool
Requires: gcc

%description
This is sample spec file created on the base of c binary packages
It is a part of Development Assistant Tool


%prep
%setup -q -n %{name}-%{version}

%build
%configure 
make %{?_smp_mflags}

%install
rm -rf ${RPM_BUILD_ROOT}
make install DESTDIR=$RPM_BUILD_ROOT

install -p -m 755 -D client ${RPM_BUILD_ROOT}%{_bindir}/client
install -p -m 755 -D server ${RPM_BUILD_ROOT}%{_bindir}/server
install -p -m 755 -D fileOperations ${RPM_BUILD_ROOT}%{_bindir}/fileOperations
install -p -m 755 -D simpleThread ${RPM_BUILD_ROOT}%{_bindir}/simpleThread
%post

%postun

%check
make check

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr(-,root,root)
%{_bindir}/client
%{_bindir}/fileOperations
%{_bindir}/server
%{_bindir}/simpleThread

%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* Fri Mar 15 2013 UserName
- first Version

