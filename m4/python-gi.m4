dnl Original credit to https://lists.gnu.org/archive/html/autoconf/2005-06/msg00104.html

dnl macro that checks for specific modules in python
AC_DEFUN([AC_PYTHON_GI_MODULE],
[AC_MSG_CHECKING(for module $1 ($2) in gi.repository)
echo "import gi; gi.require_version('$1', '$2'); from gi.repository import $1" | python3 -
if test $? -ne 0 ; then
AC_MSG_RESULT(not found)
AC_MSG_ERROR(You need the gobject-introspection binding $1)
fi
AC_MSG_RESULT(found)
])
