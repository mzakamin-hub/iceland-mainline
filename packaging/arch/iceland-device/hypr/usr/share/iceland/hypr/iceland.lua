-- OnePlus Pad 4 (iceland) settings for Omarchy's Hyprland (Lua config). iceland-hypr-setup adds one line,
--   dofile("/usr/share/iceland/hypr/iceland.lua")
-- to the end of ~/.config/hypr/hyprland.lua, so this loads after Omarchy's defaults and the user's own files.
local panel = "DSI-1"

-- 3392x2400, panel rates 144 / 120 / 90 / 60 / 50 / 48 / 30 Hz. The mode is always named, never "preferred" (= the
-- panel's first mode, 144 Hz) or "highrr". iceland-hypr-refresh keeps the rate right afterwards (power source, the
-- thermal cap, the user's choice) through wlr-output-management. Scale 2 = a 1696x1200 desktop (touch targets >= 48
-- logical px).
-- pkgrel 16 (round 10, owner 24 Nov: refresh rate and resolution settings): the start / reload rate is picked the way
-- iceland-hypr-refresh picks it, so a config reload never lands at 144 Hz unless the user chose 144, and never jumps
-- to the AC rate on battery: the user's choice (~/.config/iceland/refresh-choice: auto / 60 / 90 / 120 / 144; auto =
-- BATTERY_HZ / AC_HZ of /etc/iceland/refresh.conf, at most 120 Hz), then iceland-thermal's cap (always wins). The
-- scale is the user's own DSI-1 rule's in ~/.config/hypr/monitors.lua (Omarchy's scale control and the Display menu
-- write it there), 2 without one, so this later rule does not undo a resolution choice at the next reload.
-- Every step is guarded (pcall): an error here would abort the rest of this file.
local function iceland_read(path)
  local ok, v = pcall(function()
    local f = io.open(path, "r")
    if not f then return nil end
    local s = f:read("*a")
    f:close()
    return s
  end)
  if ok then return v end
  return nil
end
local iceland_cfg = os.getenv("XDG_CONFIG_HOME") or ((os.getenv("HOME") or "") .. "/.config")

local function iceland_start_hz()
  local c = { BATTERY_HZ = 60, AC_HZ = 120, ENABLED = 1 }
  for line in (iceland_read("/etc/iceland/refresh.conf") or ""):gmatch("[^\n]+") do
    local k, v = line:match("^%s*([%u_]+)%s*=%s*(%d+)%s*$")
    if k and c[k] ~= nil then c[k] = tonumber(v) end
  end
  local choice = (iceland_read(iceland_cfg .. "/iceland/refresh-choice") or ""):lower()
  choice = choice:gsub("%s", "")
  choice = choice:gsub("hz$", "")
  local hz
  if choice == "60" or choice == "90" or choice == "120" or choice == "144" then
    hz = tonumber(choice)                         -- a fixed choice; 144 only this way
  elseif c.ENABLED == 0 then
    hz = 120                                      -- the automatic switch is off: the historic fixed rate
  else
    -- -17: "on the charger" only when the USB supply is online AND the battery is not discharging (UPower's
    -- OnBattery, which iceland-hypr-refresh follows; -16 read only `online`, and a reload on battery landed at 120)
    local online = (iceland_read("/sys/class/power_supply/qcom-battmgr-usb/online") or ""):match("%d")
    local status = (iceland_read("/sys/class/power_supply/qcom-battmgr-bat/status") or ""):match("%a+")
    hz = (online == "1" and status ~= "Discharging") and c.AC_HZ or c.BATTERY_HZ
    if hz > 120 then hz = 120 end                 -- auto never goes above 120 Hz
  end
  local cap = tonumber((iceland_read("/run/iceland/thermal-refresh-hz") or ""):match("%d+") or "")
  if cap and cap > 0 and cap < hz then hz = cap end   -- 0 = no cap
  for _, r in ipairs({ 144, 120, 90, 60, 50, 48, 30 }) do
    if r <= hz then return r end
  end
  return 30
end

local function iceland_panel_scale()
  for line in (iceland_read(iceland_cfg .. "/hypr/monitors.lua") or ""):gmatch("[^\n]+") do
    if line:match('^%s*hl%.monitor%(%s*{%s*output%s*=%s*"DSI%-1"') then
      local s = tonumber(line:match('[{,%s]scale%s*=%s*"?([%d%.]+)"?'))
      if s and s >= 1 and s <= 4 then return s end
    end
  end
  return 2
end

local ok_hz, start_hz = pcall(iceland_start_hz)
if not ok_hz or type(start_hz) ~= "number" then start_hz = 120 end
local ok_sc, start_scale = pcall(iceland_panel_scale)
if not ok_sc or type(start_scale) ~= "number" then start_scale = 2 end
hl.monitor({ output = panel, mode = "3392x2400@" .. start_hz, position = "0x0", scale = start_scale })

-- One error in an hl.config() table aborts the whole call AND the rest of this file (24 Nov: Hyprland 0.56 moved
-- misc:vfr to debug:vfr; "unknown config key 'misc.vfr'" dropped the touch / pen mapping, blur / shadow and every
-- rule below). Every key here is checked with `Hyprland --verify-config` against the image (scripts/a1fix-verify.sh).
hl.config({
  input = {
    touchdevice = { output = panel },   -- touch follows the panel's transform (iceland-rotate)
    tablet = { output = panel },        -- the nt36536 pen likewise
  },
  misc = {
    key_press_enables_dpms = false,     -- the power key alone decides (omarchy-pad finding, 3 Nov)
  },
  debug = {
    vfr = true,                         -- no frames while nothing changes (the kernel adds its 30 Hz idle refresh)
  },
  decoration = {
    blur = { enabled = false },         -- GPU time and power on a battery device
    shadow = { enabled = false },
  },
  -- Omarchy's envs.lua sets these too; repeated here so no user ever gets the update news / donation screens,
  -- even with a personal hyprland.lua that does not load Omarchy's defaults
  ecosystem = {
    no_update_news = true,
    no_donation_nag = true,
  },
})

-- pkgrel 15 (owner 24 Nov ~13:50, gains1124/touchplugins.md item 1): Hyprland's own touch workspace swipe. A swipe
-- starts only when the finger lands within gaps_out + border_size of the panel's left / right edge (Omarchy: 10 + 2 =
-- 12 logical px; Omarchy's gaps stay as they are) and moves inward; locked sessions never swipe. Own hl.config()
-- calls: a key that a later Hyprland renames must not take the settings above with it.
-- pkgrel 16 (owner, 24 Nov): the touch swipe is OFF again. Hyprland 0.56.2 Touch.cpp drops every new touch-down while
-- a touch workspace swipe is in progress, and ends that swipe only on a touch-up with the same touch id; a cancelled or
-- lost touch-up (e.g. the pen's touch arbitration) left ALL touch dead, the lock screen's keyboard included, until a
-- reboot (24 Nov). Android-style gestures are being designed separately; the block stays so the tuning is kept.
hl.config({
  gestures = {
    workspace_swipe_touch = false,
    workspace_swipe_touch_invert = false,      -- the workspaces follow the finger, as on a phone
    workspace_swipe_distance = 300,            -- logical px for a full switch (the panel is 1696 lp wide)
    workspace_swipe_cancel_ratio = 0.2,        -- let go before 20 % (60 lp) and the switch is cancelled
    workspace_swipe_min_speed_to_force = 15,   -- a quick flick switches even below the cancel ratio
    workspace_swipe_direction_lock = true,     -- a swipe stays on its first direction
  },
})
hl.config({
  cursor = {
    hide_on_touch = true,                      -- no pointer left where the finger was
    hide_on_tablet = true,                     -- nor where the pen was
  },
})

-- stage hides windows with this tag; upstream registers the rule at run time with `hyprctl eval` (patched out, 0003).
hl.window_rule({ name = "stage-hidden", match = { tag = "stage-hidden" }, opacity = "0 override 0 override" })

-- floatkey, stage and the drawers animate themselves.
hl.layer_rule({ match = { namespace = "^floatkey$" }, no_anim = true, animation = "none" })
hl.layer_rule({ match = { namespace = "^stage$" }, no_anim = true, animation = "none" })
hl.layer_rule({ match = { namespace = "^omarchy-pad-drawers$" }, no_anim = true, animation = "none" })

-- Tablet mode (owner 24 Nov ~03:10): floating workspaces + Omarchy's dock, windows filling the area above the dock.
dofile("/usr/share/iceland/hypr/tablet-layout.lua")

-- The power key: short = Omarchy's power menu as before, hold = the power screen (owner 24 Nov ~03:45).
dofile("/usr/share/iceland/hypr/power-key.lua")

-- Deliberately absent: any `above_lock` layer rule. The lock keyboard is drawn inside the lock surface
-- (omarchy-pad-lock); an above_lock rule would let any client that names its layer like the OSK draw over the lock.
