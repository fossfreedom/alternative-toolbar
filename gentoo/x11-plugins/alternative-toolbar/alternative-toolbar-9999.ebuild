# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

EGIT_REPO_URI="https://github.com/fossfreedom/alternative-toolbar.git"

inherit eutils git-r3

DESCRIPTION="Replaces the large Rhythmbox toolbar with a client-side decorated or compact toolbar which can be hidden."
HOMEPAGE="https://github.com/fossfreedom/alternative-toolbar"
LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""
RDEPEND="
	>=media-sound/rhythmbox-3.2.1[python]
	>=dev-python/pygobject-3.16.2
	>=dev-python/lxml-3.4.1"
DEPEND="${RDEPEND}
	>=dev-vcs/git-2.4.6
	>=sys-devel/gettext-0.19.4"

src_unpack() {
	git-r3_src_unpack
}

pkg_postinst() {
	/usr/bin/glib-compile-schemas /usr/share/glib-2.0/schemas
}

pkg_postrm() {
	pkg_postinst
}
