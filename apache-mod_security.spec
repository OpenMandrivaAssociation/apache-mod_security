#Module-Specific definitions
%define mod_name mod_security
%define mod_conf 82_%{mod_name}.conf
%define mod_so %{mod_name}.so


Summary:	DSO module for the apache web server
Name:		apache-%{mod_name}
Version:	2.6.3
Release:	%mkrel 1
Group:		System/Servers
License:	Apache License
URL:		http://www.modsecurity.org/
Source0:	http://www.modsecurity.org/download/modsecurity-apache_%{version}.tar.gz
Source1:	http://www.modsecurity.org/download/modsecurity-apache_%{version}.tar.gz.asc
Source2:	mod_security.logrotate
Source3:	%{mod_conf}
Source4:	modsecurity-apache_2.5.12-rules.tar.gz
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.6
Requires(pre):	apache >= 2.2.6
Requires:	apache-conf >= 2.2.6
Requires:	apache >= 2.2.6
Requires:	apache-mod_unique_id >= 2.2.6
Requires:	mlogc >= 1.4.2
Requires:	gnupg
Requires:	unzip
Requires:	sendmail-command
BuildRequires:	apache-devel >= 2.2.6
BuildRequires:	autoconf automake libtool
BuildRequires:	curl-devel
BuildRequires:	file
BuildRequires:	libxml2-devel
BuildRequires:	lua-devel >= 5.1
BuildRequires:	pcre-devel
BuildRequires:	perl
Provides:	apache-mod_security2 = %{version}-%{release}
Obsoletes:	apache-mod_security2
Epoch:		1
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
ModSecurity is an open source intrustion detection and prevention engine for
web applications. It operates embedded into the web server, acting as a
powerful umbrella - shielding applications from attacks.

%package -n	mlogc
Summary:	ModSecurity Audit Log Collector
Group:		System/Servers

%description -n	mlogc
ModSecurity is an open source intrustion detection and prevention engine for
web applications. It operates embedded into the web server, acting as a
powerful umbrella - shielding applications from attacks.

This package contains the ModSecurity Audit Log Collector.

%prep

%setup -q -n modsecurity-apache_%{version} -a4

cp %{SOURCE2} mod_security.logrotate
cp %{SOURCE3} %{mod_conf}

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

# naming hack
pushd apache2
    find -type f | xargs perl -pi -e "s|security2|security|g"
    find -type f | xargs perl -pi -e "s|SECURITY2|SECURITY|g"
    mv mod_security2.c mod_security.c
#    mv mod_security2_config.h.in mod_security_config.h.in
popd

# since we have no *.la files
perl -pi -e "s|--link-libtool|--link-ld|g" build/find_ap*

%build
%serverbuild

rm configure
rm -rf autom4te.cache
#automake --add-missing --copy --foreign
autoreconf -fi
autoheader

%configure2_5x --localstatedir=/var/lib \
    --enable-performance-measurement \
    --enable-extentions \
    --with-apxs=%{_sbindir}/apxs \
    --with-pcre=%{_prefix} \
    --with-apr=%{_prefix} \
    --with-apu=%{_prefix} \
    --with-libxml=%{_prefix} \
    --with-lua=%{_prefix} \
    --with-curl=%{_prefix}

%make
%make -C mlogc

#%%check
#pushd apache2
#make test
#popd

%install
rm -rf %{buildroot}

install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d
install -d %{buildroot}%{_sysconfdir}/httpd/conf/modsecurity/base_rules
install -d %{buildroot}%{_sysconfdir}/httpd/conf/modsecurity/optional_rules
install -d %{buildroot}%{_sysconfdir}/logrotate.d

install -m0755 apache2/.libs/*.so %{buildroot}%{_libdir}/apache-extramodules/
install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}
install -m0644 mod_security.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{mod_name}

install -m0755 ext/.libs/mod_op_strstr.so %{buildroot}%{_libdir}/apache-extramodules/
install -m0755 ext/.libs/mod_reqbody_example.so %{buildroot}%{_libdir}/apache-extramodules/
install -m0755 ext/.libs/mod_tfn_reverse.so %{buildroot}%{_libdir}/apache-extramodules/
install -m0755 ext/.libs/mod_var_remote_addr_port.so %{buildroot}%{_libdir}/apache-extramodules/

install -m0644 rules/*.conf %{buildroot}%{_sysconfdir}/httpd/conf/modsecurity/
install -m0644 rules/base_rules/*.conf %{buildroot}%{_sysconfdir}/httpd/conf/modsecurity/base_rules/
install -m0644 rules/optional_rules/*.conf %{buildroot}%{_sysconfdir}/httpd/conf/modsecurity/optional_rules/
cp rules/CHANGELOG CHANGELOG.rules
cp rules/README README.rules

install -m0644 tools/rules-updater-example.conf %{buildroot}%{_sysconfdir}/rules-updater.conf
install -m0755 tools/rules-updater.pl %{buildroot}%{_sbindir}/

install -m0755 mlogc/mlogc %{buildroot}%{_bindir}/
install -m0755 mlogc/mlogc-batch-load.pl %{buildroot}%{_bindir}/mlogc-batch-load
install -m0644 mlogc/mlogc-default.conf %{buildroot}%{_sysconfdir}/httpd/conf/mlogc.conf

%pre
# if obsoleting apache-mod_security2
if [ -f %{_sysconfdir}/httpd/modules.d/82_mod_security2.conf ]; then
    # tuck away mod_security-1.9.x config first
    if [ -f %{_sysconfdir}/httpd/modules.d/82_mod_security.conf ]; then
	echo "old mod_security-1.9.x config file was found, renaming it to 82_mod_security-1.9.x.conf"
	mv %{_sysconfdir}/httpd/modules.d/82_mod_security.conf %{_sysconfdir}/httpd/modules.d/82_mod_security-1.9.x.conf
    fi
    mv %{_sysconfdir}/httpd/modules.d/82_mod_security2.conf %{_sysconfdir}/httpd/modules.d/%{mod_conf}
    perl -pi -e "s|security2|security|g" %{_sysconfdir}/httpd/modules.d/%{mod_conf}
    perl -pi -e "s|HAVE_SECURITY2|HAVE_SECURITY|g" %{_sysconfdir}/httpd/modules.d/%{mod_conf}
fi

if [ -f %{_sysconfdir}/logrotate.d/mod_security2 ]; then
    mv %{_sysconfdir}/logrotate.d/mod_security2 %{_sysconfdir}/logrotate.d/%{mod_name}
fi

%post
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
	if [ -f %{_var}/lock/subsys/httpd ]; then
	    %{_initrddir}/httpd restart 1>&2;
	fi
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc CHANGES LICENSE README.TXT modsecurity.conf-minimal doc/* apache2/api rules/util
%doc CHANGELOG.rules README.rules
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{mod_name}
%attr(0755,root,root) %dir %{_sysconfdir}/httpd/conf/modsecurity
%attr(0755,root,root) %dir %{_sysconfdir}/httpd/conf/modsecurity/base_rules
%attr(0755,root,root) %dir %{_sysconfdir}/httpd/conf/modsecurity/optional_rules
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity/*.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity/base_rules/*.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/modsecurity/optional_rules/*.conf
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/rules-updater.conf
%attr(0755,root,root) %{_sbindir}/rules-updater.pl
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
%attr(0755,root,root) %{_libdir}/apache-extramodules/mod_op_strstr.so
%attr(0755,root,root) %{_libdir}/apache-extramodules/mod_reqbody_example.so
%attr(0755,root,root) %{_libdir}/apache-extramodules/mod_tfn_reverse.so
%attr(0755,root,root) %{_libdir}/apache-extramodules/mod_var_remote_addr_port.so

%files -n mlogc
%defattr(-,root,root)
%doc mlogc/INSTALL
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/httpd/conf/mlogc.conf
%attr(0755,root,root) %{_bindir}/mlogc
%attr(0755,root,root) %{_bindir}/mlogc-batch-load
