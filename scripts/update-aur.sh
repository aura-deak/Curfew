#!/bin/bash
set -e

PKG_DIR="$1"
VERSION="${2#v}"

if [ -z "$PKG_DIR" ] || [ -z "$VERSION" ]; then
  echo "Usage: $0 <pkgbuild-dir> <version>"
  echo "Example: $0 aur/curfew 2.7"
  exit 1
fi

cd "$PKG_DIR"

. PKGBUILD

echo "Updating $pkgname to v$VERSION ..."

sed -i "s/^pkgver=.*/pkgver=${VERSION}/" PKGBUILD
sed -i "s/^pkgrel=.*/pkgrel=1/" PKGBUILD

# shellcheck disable=SC2154
if [ "${source[0]}" = "$pkgname-$pkgver.tar.gz::https://github.com/aura-deak/Curfew/archive/refs/tags/v$pkgver.tar.gz" ] || [ "$pkgname" = "curfew" ]; then
  SRC_URL="https://github.com/aura-deak/Curfew/archive/refs/tags/v${VERSION}.tar.gz"
  curl -sL "$SRC_URL" -o "${pkgname}-${VERSION}.tar.gz"
  SHA256=$(sha256sum "${pkgname}-${VERSION}.tar.gz" | cut -d' ' -f1)
  rm "${pkgname}-${VERSION}.tar.gz"
  sed -i "s|^sha256sums=.*|sha256sums=('${SHA256}')|" PKGBUILD
  echo "  -> sha256sums = $SHA256"
fi

# Re-source to get updated values
. PKGBUILD

generate_srcinfo() {
  local indent="\t"

  echo "pkgbase = ${pkgname}"

  for field in pkgdesc pkgver pkgrel epoch url install changelog; do
    val="${!field}"
    [ -n "$val" ] && echo -e "${indent}${field} = ${val}"
  done

  for arr in arch groups license checkdepends makedepends depends optdepends provides conflicts replaces backup source noextract validpgpkeys sha256sums md5sums; do
    eval "items=(\"\${${arr}[@]}\")"
    for item in "${items[@]}"; do
      [ -n "$item" ] && echo -e "${indent}${arr} = ${item}"
    done
  done

  for pkg in "${pkgname[@]}"; do
    echo ""
    echo "pkgname = ${pkg}"
  done
}

generate_srcinfo > .SRCINFO

echo "Done! Updated $pkgname to v$VERSION"
echo "  PKGBUILD: $PWD/PKGBUILD"
echo "  .SRCINFO: $PWD/.SRCINFO"
