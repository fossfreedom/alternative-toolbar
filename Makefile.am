%.plugin: %.plugin.in $(INTLTOOL_MERGE) $(wildcard $(top_srcdir)/po/*po)
	$(AM_V_GEN) \
	$(MKDIR_P) "$(dir $@)"; \
	$(INTLTOOL_MERGE) $(top_srcdir)/po $< $@ -d -u -c $(top_builddir)/po/.intltool-merge-cache

rb_plugin_libdir = $(libdir)/rhythmbox/plugins/alternative-toolbar

SUBDIRS = po

CLEANFILES = \
	alternative-toolbar.plugin \
	./po/.intltool-merge-cache \
	./po/Makefile \
	./po/POTFILES \
	./po/Makefile.in \
	./po/Makefile.in.in \
	./po/stamp-it \
	./m4/intltool.m4

DISTCLEANFILES = \
	alternative-toolbar.plugin \
	./po/.intltool-merge-cache \
	./po/Makefile \
	./po/POTFILES \
	./po/Makefile.in \
	./po/Makefile.in.in \
	./po/stamp-it \
	./m4/intltool.m4

PLUGIN_FILES = \
	alttoolbar_type.py \
	alttoolbar_preferences.py \
	alternative-toolbar.py \
	alttoolbar_repeat.py \
	alttoolbar_plugins.py \
	alttoolbar_widget.py \
	alttoolbar_sidebar.py \
	alttoolbar_rb3compat.py \
	alttoolbar_controller.py

IMAGE_FILES = \
	$(top_srcdir)/img/audio-radio-symbolic.svg \
	$(top_srcdir)/img/audio-x-playlist-automatic-symbolic.svg \
	$(top_srcdir)/img/audio-x-playlist-recently-added-symbolic.svg \
	$(top_srcdir)/img/audio-x-playlist-recently-played-symbolic.svg \
	$(top_srcdir)/img/audio-x-playlist-symbolic.svg \
	$(top_srcdir)/img/audio-x-queue-symbolic.svg \
	$(top_srcdir)/img/lastfm-symbolic.svg \
	$(top_srcdir)/img/librefm-symbolic.svg

UI_FILES = \
	$(top_srcdir)/ui/altlibrary.ui \
	$(top_srcdir)/ui/altpreferences.ui \
	$(top_srcdir)/ui/alttoolbar.ui

EXTRA_DIST = \
	$(PLUGIN_FILES) \
	alternative-toolbar.plugin.in \
	$(IMAGE_FILES) \
	$(UI_FILES) \
	$(top_srcdir)/po/Makefile.in.in \
	schema/org.gnome.rhythmbox.plugins.alternative_toolbar.gschema.xml \
	LICENSE

rb_plugin_lib_DATA = \
	$(PLUGIN_FILES) \
	alternative-toolbar.plugin \
	LICENSE


rb_plugin_imgdir = $(datadir)/rhythmbox/plugins/alternative-toolbar/img
rb_plugin_img_DATA = \
	$(IMAGE_FILES)

rb_plugin_uidir = $(datadir)/rhythmbox/plugins/alternative-toolbar/ui
rb_plugin_ui_DATA = \
	$(UI_FILES)

gsettings_SCHEMAS = \
	schema/org.gnome.rhythmbox.plugins.alternative_toolbar.gschema.xml

@GSETTINGS_RULES@
