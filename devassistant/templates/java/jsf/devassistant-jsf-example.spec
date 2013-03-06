Name:		devassistant-jsf-example
Version:	1.0
Release:	1%{?dist}
Summary:	Simple JavaServer Faces project

License:	GPLv2+
URL:		https://www.github.com/bkabrda/devassistant
Source0:	%{name}.tar.gz

BuildArch:      noarch

BuildRequires:	maven-local
BuildRequires:	maven-war-plugin
BuildRequires:	maven-shade-plugin
BuildRequires:	maven-clean-plugin
BuildRequires:	mojarra
BuildRequires:	maven-resources-plugin
BuildRequires:	junit4
BuildRequires:	tomcat-el-2.2-api
BuildRequires:	tomcat-jsp-2.2-api
BuildRequires:	tomcat-servlet-3.0-api
BuildRequires:	jetty-server >= 9.0.0
BuildRequires:	jetty-webapp >= 9.0.0

%description
Simple JavaServer Faces project.

%prep
%setup -q -n %{name}

%build
mvn-rpmbuild package

%install
# war
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}/webapps/
install -p -m 644 target/PROJECT_NAME.war \
  $RPM_BUILD_ROOT%{_javadir}/webapps/%{name}.war

%files
%{_javadir}/webapps/%{name}.war

%changelog
* Wed Mar 06 2013 Developer Assistant - 1.0-1
- Initial version

