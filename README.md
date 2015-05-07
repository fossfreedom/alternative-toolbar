alternative-toolbar (v0.9)
==================

Replace the Rhythmbox large toolbar with a Client-Side Decorated or Compact Toolbar which can be hidden

 - fossfreedom <foss.freedom@gmail.com>, website - https://github.com/fossfreedom

[![Flattr Button](http://api.flattr.com/button/button-compact-static-100x17.png "Flattr This!")](http://flattr.com/thing/1811704/ "fossfreedom")  [![paypaldonate](https://www.paypalobjects.com/en_GB/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=KBV682WJ3BDGL)

Replace the current standard toolbar:

![pic](http://i.imgur.com/PBFaxuv.png)

with either a compact toolbar:

![pic](http://i.imgur.com/90krK80.png)

or with the new Gnome-style client-side decoration:

![pic](http://i.imgur.com/yFUdGxn.png)

 - The compact or standard toolbar can also be toggled on or off
 - Volume Control can be switched off for all toolbars
 - Source Toolbars can be toggled - CTRL+T keyboard shortcut
 - Redesigned sidebar

The plugin preferences allows you to define which toolbars are used:

![pic](http://i.imgur.com/ozOUtSM.png)

To install the plugin:

<pre>
cd ~/Downloads
git clone https://github.com/fossfreedom/alternative-toolbar.git
cd alternative-toolbar
./install.sh
</pre>

Then enable the plugin in the plugins window.

 - From the menu use View - Show Play-Controls Toolbar
 - From the menu use View - Show Source and Media Toolbars
 - To seek forward (fast-forward) through a track - Alt+Right Cursor key
 - To seek backward through a track - Alt+Left Cursor key
 
To uninstall the plugin:

<pre>
cd alternative-toolbar
./install.sh --uninstall
</pre>

<hr/>

Thanks to the [rhythmbox-seek](https://github.com/cgarvey/rhythmbox-seek) project for the track-seeking code.

Contributors:

 - [me4oslav](https://github.com/me4oslav) - design inspiration for the header-bar vision
