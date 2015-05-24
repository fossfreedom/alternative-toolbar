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
			v0.11
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
	    <td><a href="mailto:foss.freedom@gmail.com">foss.freedom@gmail.com</a></td>
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

 - The compact or standard toolbar can also be toggled on or off
 - Volume Control can be switched off for all toolbars
 - Source Toolbars can be toggled - CTRL+T keyboard shortcut
 - Redesigned sidebar
 - Redesigned plugin window, about box and plugin preferences window
 - Repeat button can now switch between repeat tracks and repeat-one-song mode
 - Plugin translated into 18 languages and locales

The plugin preferences allows you to define which toolbars are used:

<p align="center">
    <img alt="Plugin" src="http://i.imgur.com/4Qy4fxQ.png" />
</p>

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

**Please help out with translating**

We need you to help us translate the english text to your native language.

Don't worry - it is easier that you think. Just visit:

 - https://translations.launchpad.net/alternative-toolbar

Remember to set your preferred language and then just submit your translation.

-------

Contributors:

 - [me4oslav](https://github.com/me4oslav) - design inspiration for the header-bar vision
 - our Translators: Launchpad Translation team
 
Credits:

 - [sergioad](https://github.com/sergioad) - for the initial translation (spanish) used for testing translations
 - Thanks to the [rhythmbox-seek](https://github.com/cgarvey/rhythmbox-seek) project for the track-seeking code.
 - Thanks to the [repeat-one-song](https://launchpad.net/repeat-one-song) project for the repeat-one-song code
