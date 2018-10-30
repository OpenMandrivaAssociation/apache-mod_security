#Module-Specific definitions
%define mod_name mod_security
%define mod_conf 82_%{mod_name}.conf
%define mod_so %{mod_name}.so


Summary:	DSO module for the apache web server
Name:		apache-%{mod_name}
Version:	2.7.3
Release:	12
Group:		System/Servers
License:	Apache License
URL:		http://www.modsecurity.org/
Source0:	http://www.modsecurity.org/tarball/2.7.3/modsecurity-apache_%{version}.tar.gz
Source1:	http://www.modsecurity.org/tarball/2.7.3/modsecurity-apache_%{version}.tar.gz.asc
Source2:	mod_security.logrotate
Source3:	%{mod_conf}
Source4:	modsecurity-apache_2.5.12-rules.tar.gz
Patch0:		configure.ac.patch
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
BuildRequires:	curl-devel
BuildRequires:	file
BuildRequires:	libxml2-devel
BuildRequires:	lua-devel >= 5.1
BuildRequires:	pcre-devel
BuildRequires:	perl
BuildRequires:	db-devel
Provides:	apache-mod_security2 = %{version}-%{release}
Obsoletes:	apache-mod_security2
Epoch:		1

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
%patch0 -p0
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

%build
%serverbuild

#rm configure
#rm -rf autom4te.cache
#aclocal
#automake --add-missing --copy --foreign
#autoreconf --install
#autoheader

rm -rf autom4te.cache
rm -f aclocal.m4
libtoolize --force --copy
autoreconf --install
autoheader
automake --add-missing --foreign --copy --force-missing
autoconf --force
rm -rf autom4te.cache

%configure2_5x --localstatedir=/var/lib \
    --enable-performance-measurement \
    --enable-extentions \
    --with-apxs=%{_bindir}/apxs \
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

%files
%doc CHANGES LICENSE README.TXT modsecurity.conf-minimal doc/* rules/util
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
%doc mlogc/INSTALL
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/httpd/conf/mlogc.conf
%attr(0755,root,root) %{_bindir}/mlogc
%attr(0755,root,root) %{_bindir}/mlogc-batch-load


%changelog
* Wed Oct 12 2011 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 1:2.6.2-1mdv2011.0
+ Revision: 704533
- 2.6.2

* Mon Aug 15 2011 Oden Eriksson <oeriksson@mandriva.com> 1:2.6.1-1
+ Revision: 694591
- 2.6.1

* Sat May 21 2011 Oden Eriksson <oeriksson@mandriva.com> 1:2.6.0-1
+ Revision: 676950
- 2.6.0
- ship the rules from 2.5.12 for now

* Sat May 14 2011 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.12-8
+ Revision: 674431
- rebuild

* Mon May 02 2011 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.12-7
+ Revision: 662778
- mass rebuild

* Thu Dec 02 2010 Paulo Andrade <pcpa@mandriva.com.br> 1:2.5.12-6mdv2011.0
+ Revision: 605045
- Rebuild with apr with workaround to issue with gcc type based alias analysis

* Sun Oct 24 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.12-5mdv2011.0
+ Revision: 588285
- rebuild

* Mon Mar 08 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.12-4mdv2010.1
+ Revision: 515840
- rebuilt for apache-2.2.15

* Fri Feb 26 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.12-3mdv2010.1
+ Revision: 511527
- revert -r507953

* Fri Feb 19 2010 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 1:2.5.12-2mdv2010.1
+ Revision: 507953
- rely on filetrigger for reloading apache configuration begining with 2010.1, rpm-helper macros otherwise

* Mon Feb 08 2010 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.12-1mdv2010.1
+ Revision: 502123
- 2.5.12

* Sun Nov 08 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.11-1mdv2010.1
+ Revision: 463008
- fix build
- 2.5.11

* Wed Oct 07 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 1:2.5.10-2mdv2010.0
+ Revision: 455761
- rebuild for new curl SSL backend

* Fri Sep 25 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.10-1mdv2010.0
+ Revision: 448736
- 2.5.10
- drop one redundant patch
- fix config and add more/new rules

* Sat Aug 01 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.9-2mdv2010.0
+ Revision: 406646
- rebuild

* Sat Mar 14 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.9-1mdv2009.1
+ Revision: 354887
- 2.5.9
- fix autopoo
- merge external mlogc into this package as the bundled code is newer

* Tue Jan 06 2009 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.7-2mdv2009.1
+ Revision: 326243
- rebuild

* Fri Oct 10 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.7-1mdv2009.1
+ Revision: 291384
- 2.5.7

* Sun Sep 14 2008 Oden Eriksson <oeriksson@mandriva.com> 1:2.5.6-1mdv2009.0
+ Revision: 284659
- upgrade to 2.5.6 (fixes CVE-2007-1359), actually it was renamed
  from apache-mod_security2 to apache-mod_security
- rename security2 references in the code to security

  + Michael Scherer <misc@mandriva.org>
    - better summary, fix typo in description

* Mon Jul 14 2008 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.5-6mdv2009.0
+ Revision: 235098
- rebuild

* Thu Jun 05 2008 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.5-5mdv2009.0
+ Revision: 215632
- fix rebuild
- fix buildroot

* Sun Mar 09 2008 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.5-4mdv2008.1
+ Revision: 182867
- rebuild

* Mon Feb 18 2008 Thierry Vignaud <tv@mandriva.org> 1:1.9.5-3mdv2008.1
+ Revision: 170749
- rebuild
- fix "foobar is blabla" summary (=> "blabla") so that it looks nice in rpmdrake
- kill re-definition of %%buildroot on Pixel's request

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

* Sat Sep 08 2007 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.5-2mdv2008.0
+ Revision: 82670
- rebuild

* Sun Jul 15 2007 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.5-1mdv2008.0
+ Revision: 52279
- 1.9.5


* Sat Mar 10 2007 Oden Eriksson <oeriksson@mandriva.com> 1.9.4-3mdv2007.1
+ Revision: 140742
- rebuild
- general cleanups

* Thu Nov 09 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.4-2mdv2007.0
+ Revision: 79501
- Import apache-mod_security

* Mon Aug 07 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.4-2mdv2007.0
- rebuild

* Tue May 16 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.4-1mdk
- 1.9.4
- added the generic rules and use them (S2)

* Tue Mar 14 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.2-2mdk
- fix deps

* Tue Jan 17 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.2-1mdk
- 1.9.2 (Minor feature enhancements)

* Tue Dec 13 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.1-2mdk
- rebuilt against apache-2.2.0
- fix deps

* Thu Dec 01 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.9.1-1mdk
- 1.9.1 (Minor bugfixes)
- use the common snort-rules package as source

* Wed Nov 16 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.9-1mdk
- 1.9 (Major feature enhancements)
- fix versioning

* Sun Jul 31 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_1.8.7-2mdk
- fix deps

* Fri Jun 03 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_1.8.7-1mdk
- rename the package
- the conf.d directory is renamed to modules.d
- use new rpm-4.4.x pre,post magic

* Sun Mar 20 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_1.8.7-2mdk
- use the %%mkrel macro

* Tue Mar 15 2005 Frederic Crozat <fcrozat@mandrakesoft.com> 2.0.53_1.8.7-1mdk 
- Release 1.8.7
- Fix default config file to have a working server
- Patch0: fix some snort rules

* Mon Feb 28 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_1.8.6-3mdk
- fix %%post and %%postun to prevent double restarts
- fix bug #6574

* Wed Feb 16 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_1.8.6-2mdk
- spec file cleanups, remove the ADVX-build stuff

* Tue Feb 08 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_1.8.6-1mdk
- rebuilt for apache 2.0.53

* Tue Nov 09 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_1.8.6-1mdk
- rebuilt for apache 2.0.52

* Fri Nov 05 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.8.6-1mdk
- 1.8.6

* Thu Oct 28 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.8.5-1mdk
- 1.8.5

* Fri Jul 30 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.8.4-1mdk
- 1.8.4

* Tue Jul 13 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_1.8.3-1mdk
- 1.8.3
- built for apache 2.0.50
- remove redundant provides

* Wed Jun 23 2004 Oden Eriksson <oden.eriksson@kvikkjokk.net> 2.0.49_1.8.2-1mdk
- 1.8.2

* Tue Jun 15 2004 Oden Eriksson <oden.eriksson@kvikkjokk.net> 2.0.49_1.7.6-1mdk
- built for apache 2.0.49

* Tue Mar 23 2004 Michael Scherer <misc@mandrake.org> 2.0.48_1.7.6-1mdk
- 1.7.6
- remove auto downloading of the rules

