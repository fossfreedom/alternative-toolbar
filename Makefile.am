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
    ChangeLog \
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

METAINFO_FILES = \
	$(top_srcdir)/metainfo/org.gnome.rhythmbox.rhythmbox-alternative-toolbar.addon.appdata.xml

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
	LICENSE \
	$(METAINFO_FILES)

rb_plugin_lib_DATA = \
	$(PLUGIN_FILES) \
	alternative-toolbar.plugin

rb_plugin_imgdir = $(datadir)/rhythmbox/plugins/alternative-toolbar/img
rb_plugin_img_DATA = \
	$(IMAGE_FILES)

rb_plugin_uidir = $(datadir)/rhythmbox/plugins/alternative-toolbar/ui
rb_plugin_ui_DATA = \
	$(UI_FILES)

gsettings_SCHEMAS = \
	schema/org.gnome.rhythmbox.plugins.alternative_toolbar.gschema.xml
	
rb_plugin_metainfodir = $(datadir)/metainfo
rb_plugin_metainfo_DATA = \
	$(METAINFO_FILES)

@GSETTINGS_RULES@

CHANGELOG_START = v0.14.0

ChangeLog:
	@echo Creating $@
	@if test -d "$(srcdir)/.git"; then \
	  (GIT_DIR=$(top_srcdir)/.git ./missing --run git log $(CHANGELOG_START).. --stat) > $@.tmp \
	  && mv -f $@.tmp $@ \
	  || ($(RM) $@.tmp; \
	      echo Failed to generate ChangeLog.  Your ChangeLog may be outdated >&2; \
	      (test -f $@ || echo git-log is required to generate this file >> $@)); \
	else \
	  test -f $@ || \
	  (echo A git checkout and git-log is required to generate ChangeLog >&2 && \
	  echo A git checkout and git-log is required to generate this file >> $@); \
	fi

.PHONY: ChangeLog
