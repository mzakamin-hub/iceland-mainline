// SPDX-License-Identifier: GPL-2.0-or-later
//
// iceland-bypass@oneplus-pad4: the "Bypass Charging" toggle in GNOME's Quick Settings on the OnePlus Pad 4, as stock's
// Quick Settings tile (Settings > Battery > Bypass charging). With a charger in, charging stops at the chosen
// threshold and the tablet runs from the charger (iceland-battery-guard holds the level within 1 %).
// It talks to the system service org.iceland.Bypass (iceland-bypassd; polkit org.iceland.bypass.set): Enable /
// Disable on click, SetThreshold from the menu, Refresh every minute while bypass is on (the service's request lapses
// after 5 minutes without one, as stock's), GetState every 10 seconds while the Quick Settings menu is open and every
// 30 seconds otherwise. Installed by iceland-device in /usr/share/gnome-shell/extensions and enabled by its GSettings
// override. In the lock screen extensions are disabled: no renewal, so bypass ends 5 minutes after the screen locks.
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {QuickMenuToggle, SystemIndicator} from 'resource:///org/gnome/shell/ui/quickSettings.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const BUS_NAME = 'org.iceland.Bypass';
const OBJECT_PATH = '/org/iceland/Bypass';
const BypassIface = `<node>
  <interface name="org.iceland.Bypass">
    <method name="Enable"><arg type="u" name="threshold" direction="in"/></method>
    <method name="Disable"/>
    <method name="Refresh"/>
    <method name="SetThreshold"><arg type="u" name="threshold" direction="in"/></method>
    <method name="GetState"><arg type="a{sv}" name="state" direction="out"/></method>
    <signal name="Changed"/>
  </interface>
</node>`;
const BypassProxy = Gio.DBusProxy.makeProxyWrapper(BypassIface);

// stock's threshold picker begins at 20 %
const THRESHOLDS = [20, 30, 40, 50, 60, 70, 80, 90];
const REFRESH_S = 60;
const POLL_S = 30;
const POLL_OPEN_S = 10;

const BypassToggle = GObject.registerClass(
class BypassToggle extends QuickMenuToggle {
    _init() {
        super._init({
            title: 'Bypass Charging',
            iconName: 'ac-adapter-symbolic',
            toggleMode: false,
            menuButtonAccessibleName: 'Open bypass charging menu',
        });

        this._state = null;
        this._items = new Map();

        this.menu.setHeader('ac-adapter-symbolic', 'Bypass Charging',
            'With a charger in, charging stops at the threshold and the tablet runs from the charger');
        this._section = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(this._section);
        for (const t of THRESHOLDS) {
            const item = new PopupMenu.PopupMenuItem(`Hold from ${t} %`);
            item.connect('activate', () => this._call('SetThreshold', [t]));
            this._items.set(t, item);
            this._section.addMenuItem(item);
        }
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this.menu.addSettingsAction('Power Settings', 'gnome-power-panel.desktop');

        this.connect('clicked', () => {
            if (!this._state)
                return;
            if (this._state.requested)
                this._call('Disable', []);
            else
                this._call('Enable', [this._state.threshold]);
        });

        this._proxy = new BypassProxy(Gio.DBus.system, BUS_NAME, OBJECT_PATH, (proxy, error) => {
            if (error) {
                console.warn(`iceland-bypass: ${error.message}`);
                return;
            }
            this._changedId = this._proxy.connectSignal('Changed', () => this._poll());
            this._poll();
        }, null, Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES);

        this._menuOpenId = this.menu.connect('open-state-changed', () => this._schedule());
        this._schedule();
        this._sync();
    }

    _call(method, args) {
        this._proxy[`${method}Remote`](...args, (result, error) => {
            if (error)
                Main.notifyError('Bypass Charging', error.message.replace(/^GDBus\.Error:[^ ]* /, ''));
            this._poll();
        });
    }

    _poll() {
        this._proxy?.GetStateRemote((result, error) => {
            if (error) {
                this._state = null;
            } else {
                const [dict] = result;
                const st = {};
                for (const [k, v] of Object.entries(dict))
                    st[k] = v instanceof GLib.Variant ? v.deepUnpack() : v;
                this._state = st;
            }
            this._sync();
        });
    }

    _schedule() {
        if (this._pollId)
            GLib.source_remove(this._pollId);
        const s = this.menu.isOpen ? POLL_OPEN_S : POLL_S;
        this._pollId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, s, () => {
            this._poll();
            return GLib.SOURCE_CONTINUE;
        });
        if (this.menu.isOpen)
            this._poll();
    }

    _keepAlive(on) {
        if (on && !this._refreshId) {
            this._refreshId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, REFRESH_S, () => {
                this._proxy?.RefreshRemote(() => {});
                return GLib.SOURCE_CONTINUE;
            });
        } else if (!on && this._refreshId) {
            GLib.source_remove(this._refreshId);
            this._refreshId = 0;
        }
    }

    _sync() {
        const st = this._state;
        this.visible = st !== null;
        if (!st) {
            this._keepAlive(false);
            return;
        }
        this.checked = st.requested;
        this.reactive = st.plugged || st.requested;
        if (!st.plugged)
            this.subtitle = 'Needs a charger';
        else if (st.requested && st.holding)
            this.subtitle = `Holding at ${st.level} %`;
        else if (st.requested)
            this.subtitle = `Charging to ${st.threshold} %`;
        else
            this.subtitle = `From ${st.threshold} %`;
        for (const [t, item] of this._items)
            item.setOrnament(t === st.threshold ? PopupMenu.Ornament.CHECK : PopupMenu.Ornament.NONE);
        this._keepAlive(st.requested);
    }

    destroy() {
        this._keepAlive(false);
        if (this._pollId)
            GLib.source_remove(this._pollId);
        this._pollId = 0;
        if (this._changedId)
            this._proxy.disconnectSignal(this._changedId);
        this._proxy = null;
        super.destroy();
    }
});

const BypassIndicator = GObject.registerClass(
class BypassIndicator extends SystemIndicator {
    _init() {
        super._init();
        this._toggle = new BypassToggle();
        this.quickSettingsItems.push(this._toggle);
    }

    destroy() {
        this.quickSettingsItems.forEach(item => item.destroy());
        super.destroy();
    }
});

export default class IcelandBypassExtension extends Extension {
    enable() {
        this._indicator = new BypassIndicator();
        Main.panel.statusArea.quickSettings.addExternalIndicator(this._indicator);
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
