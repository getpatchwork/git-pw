Name:           git-pw
Version:        2.3.0
Release:        1%{?dist}
Summary:        Git-Patchwork integration tool

License:        MIT
URL:            https://github.com/getpatchwork/git-pw
Source0:        %{pypi_source}

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pbr
BuildRequires:  python3-setuptools

%description
git-pw is a tool for integrating Git with Patchwork, the web-based patch
tracking system.

%prep
%autosetup -n %{name}-%{version}
# Remove bundled egg-info
rm -rf %{name}.egg-info

%generate_buildrequires
%pyproject_buildrequires -t

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files git_pw
mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 man/*.1 %{buildroot}%{_mandir}/man1/

%check
%tox

%files -f %{pyproject_files}
%license LICENSE
%doc README.rst
%{_bindir}/git-pw
%{_mandir}/man1/git-pw*.1*

%changelog
* Thu Mar 24 2022 Stephen Finucane <stephen@that.guru> - 2.3.0-1
- Update to 2.3.0

* Mon Nov 29 2021 Stephen Finucane <stephen@that.guru> - 2.2.3-1
- Update to 2.2.3

* Fri Nov 26 2021 Stephen Finucane <stephen@that.guru> - 2.2.2-1
- Update to 2.2.2

* Fri Nov 26 2021 Stephen Finucane <stephen@that.guru> - 2.2.1-1
- Update to 2.2.1

* Fri Oct 01 2021 Stephen Finucane <stephen@that.guru> - 2.2.0-1
- Update to 2.2.0

* Sun Apr 26 2020 Stephen Finucane <stephen@that.guru> - 1.9.0-1
- Initial package.
