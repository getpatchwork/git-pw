%global name git-pw
%define version 1.9.0

Name:           %{name}
Version:        %{version}
Release:        1%{?dist}
Summary:        Git-Patchwork integration tool

License:        MIT
URL:            https://github.com/getpatchwork/git-pw
Source0:        https://github.com/getpatchwork/git-pw/releases/download/%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pbr
BuildRequires:  python3-setuptools

Requires:       git
Requires:       python3-arrow
Requires:       python3-click
Requires:       python3-requests
Requires:       python3-setuptools
Requires:       python3-six
Requires:       python3-tabulate

%description
git-pw is a tool for integrating Git with Patchwork, the web-based patch \
tracking system.

%prep
%autosetup -n %{name}-%{version}
# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%py3_build

%install
%py3_install
mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 man/*.1 %{buildroot}%{_mandir}/man1/

%files
%license LICENSE
%doc README.rst
%{_bindir}/git-pw
%{_mandir}/man1/git-pw*.1.gz
%{python3_sitelib}/git_pw/
%{python3_sitelib}/git_pw-%{version}-py%{python3_version}*.egg-info

%changelog
* Sun Apr 26 2020 Stephen Finucane <stephen@that.guru> - 1.9.0-1
- Initial package.
