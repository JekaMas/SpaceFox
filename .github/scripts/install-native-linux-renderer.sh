#!/usr/bin/env bash
# Pinned native renderer prerequisite for qualification and publisher state validation.
set -euo pipefail
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]]
[[ "${ImageOS:-}" == ubuntu24 && -n "${ImageVersion:-}" ]]
readonly package_version='2.58.0+dfsg-1ubuntu0.1'
readonly package_sha256='96ca56d3b30309b594242a58094abc9adafde89456bbac64e0728553aba5769c'
readonly package_url='https://security.ubuntu.com/ubuntu/pool/universe/libr/librsvg/librsvg2-bin_2.58.0+dfsg-1ubuntu0.1_amd64.deb'
readonly dependency_dir="${RUNNER_TEMP:?}/native-linux-prerequisites"
mkdir -p "$dependency_dir"
readonly package_file="$dependency_dir/librsvg2-bin.deb"
# Failure logs are uploaded too; never retain the downloaded package there.
trap 'rm -f -- "$package_file"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 --output "$package_file" "$package_url"
printf '%s  %s\n' "$package_sha256" "$package_file" | sha256sum --check
[[ "$(stat -c %s "$package_file")" == 2300742 ]]
[[ "$(dpkg-deb -f "$package_file" Package)" == librsvg2-bin ]]
[[ "$(dpkg-deb -f "$package_file" Version)" == "$package_version" ]]
[[ "$(dpkg-deb -f "$package_file" Architecture)" == amd64 ]]
dpkg-deb --info "$package_file" > "$dependency_dir/verified-deb.txt"
# Dependencies follow this actual runner's signed Ubuntu repositories. Their
# versions and ELF bytes are measured, never described as frozen by this pin.
sudo apt-get update
sudo apt-get install --yes --no-install-recommends "$package_file"
[[ "$(dpkg-query -W -f='${Version}' librsvg2-bin)" == "$package_version" ]]
[[ "$(readlink -f "$(command -v rsvg-convert)")" == /usr/bin/rsvg-convert ]]
[[ -z "$(dpkg --verify librsvg2-bin)" ]]
rsvg-convert --version
dpkg-query -W -f='${binary:Package}\t${Version}\t${Architecture}\n' > "$dependency_dir/packages.tsv"
sha256sum "$(command -v rsvg-convert)" > "$dependency_dir/renderer.sha256"
ldd "$(command -v rsvg-convert)" > "$dependency_dir/renderer.ldd"
