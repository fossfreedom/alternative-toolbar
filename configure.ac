AC_INIT([alternative-toolbar], 0.19.0, [fossfreedom@ubuntu.com],
[alternative-toolbar], [https://github.com/fossfreedom/alternative-toolbar])
AM_INIT_AUTOMAKE([-Wno-portability no-dist-gzip dist-xz foreign subdir-objects])
AC_PREFIX_DEFAULT(/usr/local)
AM_SILENT_RULES([yes])
AC_CONFIG_MACRO_DIR([m4])

GLIB_GSETTINGS

AC_CONFIG_FILES([Makefile
                 po/Makefile.in])

IT_PROG_INTLTOOL([0.50.0])
GETTEXT_PACKAGE=alternative-toolbar
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE",
                   [The prefix for gettext translation domains.])

AM_GLIB_GNU_GETTEXT

# Pythonic checks
AM_PATH_PYTHON([3.2])

AC_PYTHON_GI_MODULE(GObject, 2.0)
AC_PYTHON_GI_MODULE(Gtk, 3.0)
AC_PYTHON_GI_MODULE(Gio, 2.0)
AC_PYTHON_GI_MODULE(RB, 3.0)
AC_PYTHON_GI_MODULE(Pango, 1.0)
AC_PYTHON_GI_MODULE(Peas, 1.0)
AC_PYTHON_GI_MODULE(PeasGtk, 1.0)
AC_PYTHON_GI_MODULE(Keybinder, 3.0)
AC_OUTPUT

AC_MSG_RESULT([
        alternative-toolbar $VERSION
        ========

        prefix:                 ${prefix}
        libdir:                 ${libdir}
        sysconfdir:             ${sysconfdir}
        exec_prefix:            ${exec_prefix}
        bindir:                 ${bindir}
        datarootdir:            ${datarootdir}
])
