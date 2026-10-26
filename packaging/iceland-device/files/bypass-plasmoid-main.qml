// SPDX-License-Identifier: GPL-2.0-or-later
// org.iceland.bypass (iceland-device-kde 0.28-36): the Plasma form of the GNOME Shell extension iceland-bypass@oneplus-pad4
// (a system-tray item). Bypass Charging talks to the system service org.iceland.Bypass (iceland-bypassd; polkit
// org.iceland.bypass.set: the active local session, no password) through busctl, as the extension does through Gio:
// GetState every 30 s (10 s while open), Enable / Disable / SetThreshold on a tap, and Refresh every 60 s while bypass
// is requested AND the session is unlocked (the service's 5-minute lease: with the item gone or the screen locked,
// bypass ends by itself, as with GNOME).
// The charge limit switch is GNOME Settings' "Preserve Battery Health": UPower's EnableChargeThreshold on the battery
// (polkit org.freedesktop.UPower.enable-charging-limit: active session, no password; thresholds 80 / 85 % from
// iceland-device's hwdb). UPower is the only writer of the kernel's thresholds; Plasma's own charge-limit setting
// (System Settings > Power Management) is refused by 49-iceland-kde-charge-limit.rules so the two never fight.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC3
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    property var st: null
    property var lim: null
    property string err: ""
    readonly property var thresholds: [20, 30, 40, 50, 60, 70, 80, 90]
    readonly property string bus: "busctl --system --json=short call org.iceland.Bypass /org/iceland/Bypass org.iceland.Bypass "
    readonly property string unlocked: "s=$(loginctl show-user \"$(id -u)\" -p Display --value); " +
                                       "[ \"$(loginctl show-session \"$s\" -p LockedHint --value)\" = no ]"
    readonly property string bat: "p=$(upower -e | grep -m1 /battery_); [ -n \"$p\" ] && "

    Plasmoid.icon: "battery-ac-adapter"
    Plasmoid.status: (st !== null && st.requested) ? PlasmaCore.Types.ActiveStatus : PlasmaCore.Types.PassiveStatus
    toolTipMainText: "Bypass Charging"
    toolTipSubText: st === null ? "service not reachable"
                  : st.requested ? (st.holding ? "on: holding at " + st.threshold + " %" : "on: from " + st.threshold + " %")
                  : (st.plugged ? "off" : "off (no charger)")

    P5Support.DataSource {
        id: exec
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => {
            disconnectSource(source)
            if (source.endsWith("# GetState")) {
                try {
                    const d = JSON.parse(data["stdout"]).data[0]
                    const o = {}
                    for (const k in d) o[k] = d[k].data
                    root.st = o
                } catch (e) {
                    root.st = null
                }
            } else if (source.endsWith("# Limit")) {
                // lines: the device path, then "b <supported>", "b <enabled>", "u <start>", "u <end>"
                const l = String(data["stdout"]).trim().split("\n")
                root.lim = (data["exit code"] === 0 && l.length >= 5)
                    ? { supported: l[1].endsWith("true"), enabled: l[2].endsWith("true"),
                        start: parseInt(l[3].split(" ")[1]), end: parseInt(l[4].split(" ")[1]) }
                    : null
            } else {
                root.err = (data["exit code"] !== 0 && data["stderr"]) ? String(data["stderr"]).trim() : ""
                poll()
            }
        }
        function run(cmd) { connectSource(cmd) }
    }

    function poll() {
        exec.run("sh -c '" + bus + "GetState' # GetState")
        exec.run("sh -c '" + bat + "echo \"$p\" && busctl --system get-property org.freedesktop.UPower \"$p\" " +
                 "org.freedesktop.UPower.Device ChargeThresholdSupported ChargeThresholdEnabled ChargeStartThreshold " +
                 "ChargeEndThreshold' # Limit")
    }
    function call(m, arg) { exec.run(bus + m + (arg === undefined ? "" : " u " + arg)) }
    function setLimit(on) {
        exec.run("sh -c '" + bat + "busctl --system call org.freedesktop.UPower \"$p\" org.freedesktop.UPower.Device " +
                 "EnableChargeThreshold b " + (on ? "true" : "false") + "' # SetLimit")
    }

    Timer {
        interval: root.expanded ? 10000 : 30000
        running: true; repeat: true; triggeredOnStart: true
        onTriggered: root.poll()
    }
    Timer {
        interval: 60000
        running: root.st !== null && root.st.requested
        repeat: true
        onTriggered: exec.run("sh -c '" + root.unlocked.replace(/'/g, "'\\''") + " && " + root.bus + "Refresh' # Refresh")
    }

    fullRepresentation: ColumnLayout {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 16
        spacing: Kirigami.Units.smallSpacing
        PC3.Label {
            Layout.fillWidth: true; wrapMode: Text.WordWrap
            text: "With a charger in, charging stops at the threshold and the tablet runs from the charger."
        }
        PC3.Switch {
            text: "Bypass Charging"
            enabled: root.st !== null && (root.st.plugged || root.st.requested)
            checked: root.st !== null && root.st.requested
            onToggled: checked ? root.call("Enable", root.st.threshold) : root.call("Disable")
        }
        PC3.ComboBox {
            Layout.fillWidth: true
            model: root.thresholds.map(t => "Hold from " + t + " %")
            currentIndex: root.st === null ? 0 : Math.max(0, root.thresholds.indexOf(root.st.threshold))
            onActivated: (i) => root.call("SetThreshold", root.thresholds[i])
        }
        PC3.Label {
            Layout.fillWidth: true; wrapMode: Text.WordWrap; opacity: 0.7
            text: root.st === null ? "org.iceland.Bypass is not reachable"
                : "Battery " + root.st.soc + " %, charger " + (root.st.plugged ? "in" : "out")
                  + (root.st.holding ? ", holding" : "") + (root.err ? "\n" + root.err : "")
        }
        Kirigami.Separator { Layout.fillWidth: true }
        PC3.Switch {
            text: root.lim !== null && root.lim.supported
                  ? "Charge limit (stop at " + root.lim.end + " %, resume below " + root.lim.start + " %)"
                  : "Charge limit (not available)"
            enabled: root.lim !== null && root.lim.supported
            checked: root.lim !== null && root.lim.enabled
            onToggled: root.setLimit(checked)
        }
    }
}
