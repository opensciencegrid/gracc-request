Name:           gracc-request
Version:        1.0
Release:        1%{?dist}
Summary:        GRACC Listener for Raw and Summary Records

License:        ASL 2.0
URL:            https://opensciencegrid.github.io/gracc/
Source0:        gracc-request-%{version}.tar.gz

BuildRequires:  python-setuptools
BuildRequires:  systemd
Requires:       python2-pika
Requires:       python-elasticsearch-dsl
Requires:       python-dateutil
Requires(pre):  shadow-utils

%description
GRACC Listener for Raw and Summary Records

%package -n %{name}-client
Summary:        GRACC Listener Client
Requires:       python2-pika
Requires:       python-dateutil
%description -n %{name}-client
GRACC Listener for Raw and Summary Records


%pre
getent group gracc >/dev/null || groupadd -r gracc
getent passwd gracc >/dev/null || \
    useradd -r -s -g gracc -d /tmp -s /sbin/nologin \
    -c "GRACC Services Account" gracc
exit 0

%prep
%setup -q


%build
%py2_build


%install
%py2_install


install -d -m 0755 %{_sysconfdir}/graccreq/config.d/
install -m 0744 config/gracc-request-test.toml %{_sysconfdir}/graccreq/config.d/gracc-request.toml
install -d -m 0755 %{_unitdir}
install -m 0744 config/graccreq.service %{_unitdir}



%files
%{python2_sitelib}/graccreq
%{_bindir}/*
%{_unitdir}/*
%config %{_sysconfdir}/*

%doc



%changelog


