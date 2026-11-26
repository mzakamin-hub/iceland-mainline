-- OnePlus Pad 4: the power key (owner 24 Nov ~03:45: upstream omarchy-pad's power screen, on a HOLD only).
-- Omarchy binds XF86PowerOff to its power menu ({ menu = "system" }, locked = true, bindings/utilities.lua); logind
-- ignores the key (Omarchy's HandlePowerKey=ignore, unchanged). Here the same key becomes press / release halves
-- (Omarchy's own o.bind_hold) of iceland-power-key:
--   short press: exactly Omarchy's power menu as before (omarchy-menu toggle system), now on the release instead of
--                the press (a hold has to be told apart); with the power screen open, a short press closes it
--   hold 0.6 s:  the power screen (omarchy-pad.power plugin: Power off / Restart / Lock) - never on the lock screen
--                (as upstream: no menu over the lock, so no way around it)
-- Not taken from upstream: its sleep-on-short-press, the handle-power-key inhibitor, the Volume Down screenshot combo.
if o and o.bind_hold then
  hl.unbind("XF86PowerOff")
  o.bind_hold("XF86PowerOff", "Power menu (hold: power screen)", "/usr/libexec/iceland/iceland-power-key press",
    "Power button released", "/usr/libexec/iceland/iceland-power-key release", { locked = true })
end
