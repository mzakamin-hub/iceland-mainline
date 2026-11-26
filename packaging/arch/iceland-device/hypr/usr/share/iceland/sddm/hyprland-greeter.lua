-- The SDDM Wayland greeter's compositor on the OnePlus Pad 4: Omarchy's greeter config (keyboard layout logic,
-- no animations) plus the panel at 60 Hz (never "preferred": the panel offers 144 Hz) and touch mapped to it.
-- The password keys are drawn by the theme (omarchy-iceland). wvkbd (iceland-greeter-osk) is the fallback, started
-- only with GREETER_OSK=wvkbd in /etc/iceland/greeter-osk.conf (default: theme).
dofile("/usr/share/sddm/hyprland.lua")
hl.monitor({ output = "DSI-1", mode = "3392x2400@60", position = "0x0", scale = 2 })
hl.config({ input = { touchdevice = { output = "DSI-1" } } })

local function greeter_osk()
  local file = io.open("/etc/iceland/greeter-osk.conf", "r")
  if not file then
    return "theme"
  end
  local value = "theme"
  for line in file:lines() do
    local v = line:match("^%s*GREETER_OSK%s*=%s*[\"']?([%w_-]+)[\"']?%s*$")
    if v then
      value = v
    end
  end
  file:close()
  return value
end

if greeter_osk() == "wvkbd" then
  hl.on("hyprland.start", function()
    hl.exec_cmd("/usr/libexec/iceland/iceland-greeter-osk")
  end)
end
