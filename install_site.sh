#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

usage() {
  echo Usage:
  echo "    install_site.sh [Options] ... CFG_file"
  echo
  echo "CFG_file - is the name of the installation configuration file which contains"
  echo "           all the instructions for the DIRAC installation. See DIRAC Administrator "
  echo "           Guide for the details"
  echo ""
  echo "Options:"
  echo "    -i, --install-root       The root of the DIRAC installation, defaults to $PWD"
  echo "    -e, --extension          Use an extension instead of vanilla DIRAC"
  echo "    -v, --version            Choose a specific version instead of getting the latest stable version from PyPI"
  echo "    -p, --extra-pip-install  Install additional packages (e.g. WebAppDIRAC), can be passed multiple times"
  echo "    -h, --help     print this"
  exit 1
}

install_root="${PWD}"
extension="DIRAC"
version=""
install_cfg=""
declare -a extra_pip_install

# Parse the arguments
while [ "${1:-}" ]; do
  case "${1}" in

  -h | --help )
    usage
    exit
  ;;

  -i | --install-root )
    switch=${1}
    shift
    [ "${1}" ] || error_exit "Switch ${switch} requires a argument"
    install_root=${1}
  ;;

  -e | --extension )
    switch=${1}
    shift
    [ "${1}" ] || error_exit "Switch ${switch} requires a argument"
    extension=${1}
  ;;

  -v | --version )
    switch=${1}
    shift
    [ "${1}" ] || error_exit "Switch ${switch} requires a argument"
    version=${1}
  ;;

  -p | --extra-pip-install )
    switch=${1}
    shift
    [ "${1}" ] || error_exit "Switch ${switch} requires a argument"
    extra_pip_install+=("${1}")
  ;;

  * )
    if [[ "${install_cfg}" != "" ]]; then
      echo "ERROR: Multiple CFG files specified: ${install_cfg} and ${1}"
      exit 1
    fi
    install_cfg=${1}
  ;;

  esac
  shift
done

# Validate the arguments
if [[ "${install_cfg}" == "" ]]; then
  usage
  exit 1
fi

if [[ -z "${version}" ]]; then
  api_url=https://pypi.org/pypi/$extension/json
  version=$(curl --silent -L "${api_url}" | sed 's@,@\n@g' | grep '"version"' | cut -d ':' -f 2)
  if [[ "${version}" != \"*.*\" ]]; then
    echo "ERROR: Failed to find a version from ${api_url}"
    exit 1
  fi
  version=${version:1:-1}
  echo "Detected latest version of ${extension} as ${version}"
fi

version_and_date="v${version}-$(date -u '+%s')"
platform="$(uname -s)-$(uname -m)"

# Download and install DIRACOS
mkdir -p "${install_root}/versions"
cd "${install_root}"
curl -LO "https://github.com/DIRACGrid/DIRACOS2/releases/latest/download/DIRACOS-${platform}.sh"
install_diracos_root="${install_root}/versions/${version_and_date}/${platform}"
bash "DIRACOS-${platform}.sh" -p "${install_diracos_root}"
rm "DIRACOS-${platform}.sh"
source "${install_diracos_root}/diracosrc"

# Install DIRAC
declare -a pip_install_args
pip_install_args+=("${extension}[server]==${version}")
if [[ "$(grep WebPortal "${install_cfg}" | cut -d '=' -f 2 | tr -d " ")" == "yes" ]]; then
  pip_install_args+=("WebAppDIRAC[server]")
fi
pip install "${pip_install_args[@]}"
if (( ${#extra_pip_install[@]} )); then
  echo Installing extra pip packages with "${extra_pip_install[@]}"
  pip install "${extra_pip_install[@]}"
fi

# Finish off the installation
ln -s "${install_root}/versions/${version_and_date}" "${install_root}/pro"
{
  echo 'default_dirac="'"${install_root}"'/pro/$(uname -s)-$(uname -m)"'
  echo 'if [ -n "${DIRAC:-}" ] && [[ "${default_dirac}" != "${DIRAC:-}" ]]; then'
  echo '    echo DIRAC installation path overriden to ${DIRAC}'
  echo 'fi'
  echo 'export DIRAC=${DIRAC:-${default_dirac}}'
  echo 'unset default_dirac'
  echo ''
  echo '# CAs path for SSL verification'
  echo 'export X509_CERT_DIR=${X509_CERT_DIR:-"'"${install_root}/etc/grid-security/certificates"'"}'
  echo 'export X509_VOMS_DIR=${X509_VOMS_DIR:-"'"${install_root}/etc/grid-security/vomsdir"'"}'
  echo 'export X509_VOMSES=${X509_VOMSES:-"'"${install_root}/etc/grid-security/vomses"'"}'
  echo ''
  echo '. $DIRAC/diracosrc'
} > "${install_root}/bashrc"
source "${install_root}/bashrc"

# Configure and set up the site
dirac-configure --cfg "${install_cfg}" -ddd
dirac-setup-site -ddd
