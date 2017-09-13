<table width="100%">
	<tr>
		<th align="left" width="60%">
			alternative-toolbar
		</th>
		<th width="10%">
			Version
		</th>
		<th align="right" width="30%">
			Support
		</th>
	</tr>
	<tr>
	    <td width="60%" rowspan="3">
	        Replace the Rhythmbox large toolbar with a Client-Side Decorated or Compact toolbar which can be hidden.
	    </td>
		<td align="center" width="10%">
			v0.17.5
		</td>
		<td align="right" width="30%">
		    <a href="http://flattr.com/thing/1811704/" title="fossfreedom">
		        <img alt="Flattr This!" src="http://api.flattr.com/button/button-compact-static-100x17.png" />
		    </a>
		    <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=KBV682WJ3BDGL" title="PayPal Donate">
		        <img alt="PayPal Donate" src="https://www.paypalobjects.com/en_GB/i/btn/btn_donate_SM.gif" />
		    </a>
		</td>
	</tr>
	<tr>
	    <td><b>Email</b></td>
	    <td><a href="mailto:fossfreedom@ubuntu.com">fossfreedom@ubuntu.com</a></td>
	</tr>
	<tr>
	    <td><b>Website</b></td>
	    <td><a href="https://github.com/fossfreedom">https://github.com/fossfreedom</a></td>
		</td>
	</tr>
</table>

Replace the current standard toolbar:

![pic](http://i.imgur.com/9FjnAd5.png)

with either a compact toolbar:

![pic](http://i.imgur.com/5XqQKcG.png)

or with the new Gnome-style client-side decoration:

![pic](http://i.imgur.com/rMkxjxw.png)


## Features
 - Option to prefer dark-themes
 - Display Browse Categories horizontally or vertically
 - Move columns via Drag-and-Drop using a views' column headers
 - Toggle compact or standard toolbar on or off
 - Volume Control can be switched on or off for all toolbars
 - Source Toolbars can be toggled (`CTRL + T`)
 - Seek forward (fast-forward) through a track (`ALT + Right Arrow`)
 - Seek backward through a track (`ALT + Left Arrow`)
 - Redesigned sidebar
 - Redesigned plugin window, about box and plugin preferences window
 - Repeat button can now switch between repeat tracks and repeat-one-song mode
 - Force display of the app-menu (compact/headerbar)
   `gsettings set org.gnome.rhythmbox.plugins.alternative_toolbar 
  app-menu-display true`
 - Plugin translated completely into [14 languages and locales (18 more on the
  way)](https://translations.launchpad.net/alternative-toolbar)

The plugin preferences allows you to define which toolbars are used:

<p align="center">
    <img alt="Plugin" src="http://i.imgur.com/4Qy4fxQ.png" />
</p>

## Keyboard shortcuts
| Key                 | Action                                       |
|---------------------|----------------------------------------------|
| `CTRL + T`          | Toggled source toolbar.                      |
| `CTRL + F`          | Toggle search bar.                           |
| `CTRL + P`          | Start/Stop current track.                    |
| `CTRL + R`          | Open repeat menu.                            |
| `CTRL + K`          | Toggle play queue.                           |
| `CTRL + A/?`        | Select all songs in playlist.                |
| `ALT + Right Arrow` | Seek forward (fast-forward) through a track. |
| `ALT + Left Arrrow` | Seek backward through a track.               |

After installation enable the plugin in the plugins window:
<p align="center">
    <img alt="Enable plugin" src="http://i.imgur.com/UUzyfhH.png" />
</p>

If you need to enable the player controls & source menu, this can be done from the menu:

 - Menu ->
   - View ->
     - Show Play-Controls Toolbar
     - Show Source and Media Toolbars

## Installation
**Latest Stable Release via source code compilation**
Navigate to the archive and grab the newest .tar.gz from https://github.com/fossfreedom/alternative-toolbar/releases
```bash
cd ~/Downloads
sudo apt-get install intltool git gir1.2-glib-2.0 gir1.2-gstreamer-1.0 gir1.2-gtk-3.0 gir1.2-peas-1.0 gir1.2-rb-3.0 gnome-pkg-tools gobject-introspection libglib2.0-dev pkg-config python3-gi python3
tar -zxvf alternative-toolbar*.tar.gz
cd alternative-toolbar*
./autogen.sh --prefix=/usr
make
sudo make install
```

This will install a system-wide installation.  If you have a previous locally installed
version of the plugin, remove it:

```
rm -rf ~/.local/share/rhythmbox/plugins/alternative-toolbar
```

**Install Latest Development Release via Git**
```bash
cd ~/Downloads
sudo apt-get install intltool git gir1.2-glib-2.0 gir1.2-gstreamer-1.0 gir1.2-gtk-3.0 gir1.2-peas-1.0 gir1.2-rb-3.0 gnome-pkg-tools gobject-introspection libglib2.0-dev pkg-config python3-gi python3
git clone https://github.com/fossfreedom/alternative-toolbar.git
cd alternative-toolbar
./autogen.sh --prefix=/usr
make
sudo make install
```

This will install a system-wide installation.  If you have a previous locally installed
version of the plugin, remove it:

```
rm -rf ~/.local/share/rhythmbox/plugins/alternative-toolbar
```

**Ubuntu PPA - latest stable release**

If you are using Ubuntu you can install alternative-toolbar via a [PPA](https://launchpad.net/~fossfreedom/+archive/ubuntu/rhythmbox-plugins).
```bash
sudo add-apt-repository ppa:fossfreedom/rhythmbox-plugins
sudo apt-get update
sudo apt-get install rhythmbox-plugin-alternative-toolbar
```

**Arch AUR - latest development release**

If you are using Arch you can install alternative-toolbar via the [rhythmbox-plugin-alternative-toolbar-git](https://aur.archlinux.org/packages/rhythmbox-plugin-alternative-toolbar-git/) package

**Gentoo ebuild**

If you are using Gentoo you can install alternative-toolbar by adding the ebuild located in the gentoo branch `gentoo/x11-plugins/alternative-toolbar` to your local overlay (`/usr/local/portage`).

i.e. 

```
git clone https://github.com/fossfreedom/alternative-toolbar -b gentoo

add the ebuild

git checkout master
```

Use the following to ebuild

```
$ ebuild alternative-toolbar-9999.ebuild digest
$ emerge alternative-toolbar
```

## To uninstall.

If installed via Git you need the original code to uninstall the plugin.
```bash
cd ~/Downloads/alternative-toolbar*
sudo make uninstall
```

## Contribute
**Please help out with translating**

We need you to help us translate the english text to your native language.

Don't worry - it is easier that you think. Just visit:

 - https://translations.launchpad.net/alternative-toolbar

Remember to set your preferred language and then just submit your translation.

## Credits
Thank you to:

 - [me4oslav](https://github.com/me4oslav) - design inspiration for the header-bar vision
 - our Translators: Launchpad Translation team
 - [Julian Richen](https://github.com/julianrichen) - revamped README
 - [Ikey Doherty](https://github.com/ikeydoherty) - AutoTools installer
 
As well as:

 - [sergioad](https://github.com/sergioad) - for the initial translation (spanish) used for testing translations
 - Thanks to the [rhythmbox-seek](https://github.com/cgarvey/rhythmbox-seek) project for the track-seeking code.
 - Thanks to the [repeat-one-song](https://launchpad.net/repeat-one-song) project for the repeat-one-song code
 - [gipawu](https://github.com/gipawu) - improved progress slider code
