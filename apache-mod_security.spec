#Module-Specific definitions
%define mod_name mod_security
%define mod_conf 82_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	Mod_security is a DSO module for the apache web server
Name:		apache-%{mod_name}
Version:	1.9.5
Release:	%mkrel 1
Group:		System/Servers
License:	GPL
URL:		http://www.modsecurity.org/
Source0:	http://www.modsecurity.org/download/modsecurity-apache_%{version}.tar.gz
Source1:	http://www.modsecurity.org/download/modsecurity-apache_%{version}.tar.gz.asc
Source2:	http://www.modsecurity.org/download/modsecurity-rules-current.tar.gz
Source3:	%{mod_conf}
# (fc) 1.8.7-1mdk fix some snort rules
Patch0:		modsecurity-apache-1.9.1-web-attacks.rules.diff
Patch1:		modsecurity-apache-1.9.1-web-php.rules.diff
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.4
Requires(pre):	apache >= 2.2.4
Requires:	apache-conf >= 2.2.4
Requires:	apache >= 2.2.4
BuildRequires:	apache-devel >= 2.2.4
BuildRequires:	file
BuildRequires:	snort-rules
Epoch:		1
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

%description
ModSecurity is an open source intrustion detection and prevention
engine for web applications. It operates embedded into the web
server, acting as a powerful umbrella - shielding applications
from attacks.

%prep

%setup -q -n modsecurity-apache_%{version} -a2
cp %{_sysconfdir}/snort/rules/web*.rules .

%patch0 -p0 -b .web-attacks
%patch1 -p0 -b .web-php

cat > mod_security-snortrules.conf << EOF
# This file was generated using the %{_sbindir}/snort2modsec.pl perl script like so:
# 1. urpmi snort-rules
# 2. snort2modsec.pl /etc/snort/rules/web*.rules >> /etc/httpd/conf/mod_security-snortrules.conf

EOF
perl util/snort2modsec.pl web*.rules >> mod_security-snortrules.conf

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

# fix attribs
find doc -type f -exec chmod 644 {} \;

cp %{SOURCE3} %{mod_conf}


%build
cp apache2/%{mod_name}.c .
%{_sbindir}/apxs -c %{mod_name}.c

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d

install -m0755 .libs/*.so %{buildroot}%{_libdir}/apache-extramodules/
install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_sysconfdir}/httpd/conf

install -m0755 util/snort2modsec.pl %{buildroot}%{_sbindir}/
install -m0644 mod_security-snortrules.conf %{buildroot}%{_sysconfdir}/httpd/conf/

install -m0644 modsecurity-experimental.conf %{buildroot}%{_sysconfdir}/httpd/conf/
install -m0644 modsecurity-general.conf %{buildroot}%{_sysconfdir}/httpd/conf/
install -m0644 modsecurity-hardening.conf %{buildroot}%{_sysconfdir}/httpd/conf/
install -m0644 modsecurity-output.conf %{buildroot}%{_sysconfdir}/httpd/conf/
install -m0644 modsecurity-php.conf %{buildroot}%{_sysconfdir}/httpd/conf/

%post
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc CHANGES INSTALL README httpd.conf* doc/*
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/mod_security-snortrules.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity-experimental.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity-general.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity-hardening.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity-output.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity-php.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
%attr(0755,root,root) %{_sbindir}/snort2modsec.pl
