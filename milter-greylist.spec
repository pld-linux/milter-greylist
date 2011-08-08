#
# Conditional build:
%bcond_with		spf
%bcond_with		libbind

Summary:	Milter for greylisting, the next step in the spam control war
Name:		milter-greylist
Version:	4.2.7
Release:	0.2
License:	BSD with advertising
Group:		Daemons
URL:		http://hcpnet.free.fr/milter-greylist/
Source0:	ftp://ftp.espci.fr/pub/milter-greylist/%{name}-%{version}%{?beta}.tgz
# Source0-md5:	a47d70e0b8a73d341f0d511b3f693650
Source1:	%{name}.init
Patch4:		ai_addrconfig.patch
Patch7:		%{name}-dkim-reentrant.patch
# http://tech.groups.yahoo.com/group/milter-greylist/message/5551
Patch8:		cloexec.patch
# http://tech.groups.yahoo.com/group/milter-greylist/message/5564
Patch9:		spamd-null.patch
Patch10:	config.patch
BuildRequires:	GeoIP-devel
BuildRequires:	autoconf
BuildRequires:	bison
BuildRequires:	curl-devel
BuildRequires:	flex
%{?with_libbind:BuildRequires:	libbind-devel}
BuildRequires:	libmilter-devel
%{?with_spf:BuildRequires:	libspf-devel}
BuildRequires:	m4
BuildRequires:	rpmbuild(macros) >= 1.202
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Provides:	group(%{username})
Provides:	user(%{username})
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		username	grmilter
%define		vardir		%{_var}/lib/%{name}
%define		dbdir		%{vardir}/db
%define		rundir		%{_var}/run/%{name}

%description
Greylisting is a new method of blocking significant amounts of spam at
the mailserver level, but without resorting to heavyweight statistical
analysis or other heuristical (and error-prone) approaches.
Consequently, implementations are fairly lightweight, and may even
decrease network traffic and processor load on your mailserver.

This package provides a greylist filter for sendmail's milter API.

%prep
%setup -q
%patch4 -p1
%patch7 -p1
%patch8 -p1
%patch9 -p1
%patch10 -p1

%{__sed} -i -e 's!/libresolv.a!/../../../no-such-lib.a!g' configure.ac

# drop rpath and wrong lib dir
%{__sed} -i -e 's#-L$withval/lib -Wl,$rpath$withval/lib##' configure.ac

grep -rl /var/milter-greylist . | xargs sed -i -e '
	s!/var/milter-greylist/milter-greylist.sock!%{rundir}/milter-greylist.sock!g;
	s!/var/milter-greylist/greylist.db!%{dbdir}/greylist.db!g;
	s!/var/milter-greylist/milter-greylist.pid!%{_var}/run/milter-greylist.pid!g;
'

%build
%{__aclocal}
%{__autoconf}
%{__autoheader}
%configure \
	--disable-rpath \
	--with-user=%{username} \
	--enable-dnsrbl \
	--enable-spamassassin \
	--enable-p0f \
	--disable-drac \
	--with-drac-db=%{vardir}/drac/drac.db \
	--with-libGeoIP=/usr \
	--with-libcurl=/usr \
	%{?with_libbind:--with-libbind=/usr} \
	%{?with_spf:--with-libspf=/usr}
## is not SMP safe :(
%{__make} -j1 \
	TEST=false \
	BINDIR=%{_sbindir}

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT{%{rundir},%{dbdir},%{_var}/run,/etc/rc.d/init.d}
%{__make} install \
	TEST=false \
	USER=%(id -u) \
	BINDIR=%{_sbindir} \
	DESTDIR=$RPM_BUILD_ROOT

install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}

# create temporary files
touch $RPM_BUILD_ROOT%{rundir}/milter-greylist.sock
touch $RPM_BUILD_ROOT%{_var}/run/milter-greylist.pid

%pre
%groupadd -g 7 -r %{username}
%useradd -u 7 -r -s /sbin/nologin -M -d %{vardir} -c 'Greylist-milter user' -g %{username} %{username}

%postun
if [ "$1" = "0" ]; then
	%userremove  %{username}
	%groupremove %{username}
fi

%post
/sbin/chkconfig --add %{name}
%service %{name} restart

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc ChangeLog README
%attr(640,root,%{username}) %verify(not mtime) %config(noreplace) %{_sysconfdir}/mail/greylist.conf
%attr(754,root,root) /etc/rc.d/init.d/milter-greylist
%attr(755,root,root) %{_sbindir}/milter-greylist
%{_mandir}/man5/greylist.conf.5*
%{_mandir}/man8/milter-greylist.8*
%dir %attr(751,%{username},%{username}) %{vardir}
%dir %attr(770,root,%{username}) %{dbdir}
%dir %attr(710,%{username},mail) %{rundir}
%ghost %{rundir}/milter-greylist.sock
%ghost %{_var}/run/milter-greylist.pid
