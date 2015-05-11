DESTDIR=
SUBDIR=/usr/lib/rhythmbox/plugins/alternative-toolbar/
DATADIR=/usr/share/rhythmbox/plugins/alternative-toolbar/
LOCALEDIR=/usr/share/locale/
GLIB_SCHEME=org.gnome.rhythmbox.plugins.alternative_toolbar.gschema.xml
GLIB_DIR=/usr/share/glib-2.0/schemas/


all:
clean:
	- rm *.pyc

install:
	install -d $(DESTDIR)$(SUBDIR)
	install -m 644 *.py $(DESTDIR)$(SUBDIR)
	install -m 644 LICENSE $(DESTDIR)$(SUBDIR)
	install -d $(DESTDIR)$(DATADIR)img
	install -m 644 img/*.svg $(DESTDIR)$(DATADIR)img/
	install -d $(DESTDIR)$(DATADIR)ui
	install -m 644 ui/*.ui $(DESTDIR)$(DATADIR)ui/
	install -m 644 alternative-toolbar.plugin* $(DESTDIR)$(SUBDIR)
	install -d $(DESTDIR)$(GLIB_DIR)
	install -m 644 schema/$(GLIB_SCHEME) $(DESTDIR)$(GLIB_DIR) 
	cd po;./install_all.sh $(DESTDIR)$(LOCALEDIR)
