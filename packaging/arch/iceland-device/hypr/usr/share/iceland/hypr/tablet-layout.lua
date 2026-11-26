-- OnePlus Pad 4: tablet mode = floating workspaces with Omarchy's dock, windows filling the screen above the dock
-- (owner 24 Nov ~03:10). Loaded by iceland.lua after Omarchy's defaults. The layout itself is Omarchy's own:
-- /usr/libexec/iceland/iceland-tablet-layout writes Omarchy's workspace-layouts/default.lua (floating | none) when
-- /run/iceland/mode changes and reloads; Omarchy's workspace-modes.lua then floats / re-tiles the windows it claims
-- (tags omarchy-mode-floated / -opened) and shows its dock on floating workspaces. This file only changes the SIZE
-- Omarchy gives such windows in tablet mode: instead of a 64 % centred float, the whole area above the dock
-- (iPad-like). Dialogs and apps that float on their own never get Omarchy's open tag, so they keep their size.
--
-- pkgrel 19 (owner 24 Nov: "the dock seems to be inconsistent as well as the floating mode"; "when the app is full
-- screen the handle to drag it back to floating window is too thin"):
--  * Omarchy's titlebar (omarchy-hyprland-titlebars = hyprbars, a STICKY top decoration) is drawn ABOVE a floating
--    window's box (Hyprland 0.56.2 WindowTarget: floating windows get their box as is, only tiled / maximized ones are
--    shrunk by the reserved decoration area). -18 put the box 8 px under the top bar, so 22 of the 30 px titlebar lay
--    under the bar and only 8 px were left to grab. The fit now puts the box below the WHOLE titlebar, and in tablet
--    mode the titlebar is finger sized (TITLEBAR_PX panel pixels, ~7 mm: 44 logical px at scale 2).
--  * The space kept for the dock is the dock's real depth (Omarchy's DockWindow.qml: gap + icon slot, both following
--    the shell's [font] base-size / [spacing]), checked against the live omarchy-dock layer, instead of a fixed 84.
--  * floatkey's docked keyboard reserves the bottom edge while shown (exclusive zone ~396 px). A refit in that moment
--    (a refresh modeset during the smoke tests) shrank the window and nothing grew it back. Bottom reservations of
--    OSK_MIN px or more are the keyboard and are ignored; the position is absolute (Hyprland's centre would follow
--    the keyboard's work area); windows are also refitted when a layer surface opens / closes.
--  * A window the owner moved or resized after a fit is never refitted (except at a mode change, as before): each fit
--    records the geometry it gave and the monitor's logical size in a tag (iceland-fit-<x>_<y>_<w>x<h>_<mw>x<mh>); a
--    window that no longer has that geometry loses the fit tags. -18 windows without the record are fitted once more.
local MODE_FILE = rawget(_G, "ICELAND_TABLET_MODE_FILE") or "/run/iceland/mode"   -- the global: logic tests only
local OPENED_TAG = "omarchy-mode-opened"   -- Omarchy's open rule placed it (non-modal, not a floating-on-its-own app)
local FLOATED_TAG = "omarchy-mode-floated" -- Omarchy floated it because its workspace is floating
local WORKSPACE_TAG = "omarchy-floating-workspace" -- on a floating workspace: Omarchy's titlebar follows this tag
local FIT_TAG = "iceland-tablet-fit"       -- fitted by us (refitted after a rotation / a reserved-area change)
local RECORD = "iceland-fit-"              -- iceland-fit-<x>_<y>_<w>x<h>: the geometry of our last fit
local GAP = 8                              -- logical px around a fitted window (under the bar, sides, above the dock)
local OSK_MIN = 120                        -- a bottom reservation this tall is floatkey's docked keyboard, not a bar
local TITLEBAR_PX = 88                     -- the titlebar in panel pixels in tablet mode (~7 mm at 315 ppi)
local TITLEBAR_MIN, TITLEBAR_MAX = 30, 96  -- logical px: Omarchy's own 30 at least
local TOLERANCE = 2
local HOME = os.getenv("HOME") or ""
local REFIT = (os.getenv("XDG_STATE_HOME") or (HOME .. "/.local/state")) .. "/iceland/tablet-refit-pending"
local CONFIG_HOME = os.getenv("XDG_CONFIG_HOME") or (HOME .. "/.config")
-- Omarchy's shell reads the theme's shell.toml under ~/.local/state whatever XDG_STATE_HOME says, then the user's
local SHELL_TOML = { HOME .. "/.local/state/omarchy/current/theme/shell.toml", CONFIG_HOME .. "/omarchy/shell.toml" }

local M = {}

local function round(x)                    -- JavaScript's Math.round for the shell's geometry
  return math.floor(x + 0.5)
end

local function read(path)
  local f = io.open(path, "r")
  if not f then
    return nil
  end
  local s = f:read("*a")
  f:close()
  return s
end

local function tablet()
  local mode = read(MODE_FILE)
  return mode ~= nil and mode:match("^%s*(%S*)") == "tablet"
end

local function has_tag(window, tag)
  for _, t in ipairs(window.tags or {}) do
    if t == tag or t == tag .. "*" then
      return true
    end
  end
  return false
end

-- ---- the dock's depth (Omarchy shell: DockWindow.qml + Commons/Style.qml) ----

-- "[section]" + "key = value" lines of shell.toml, as "section.key" -> raw string (the later file wins)
local function shell_values()
  local values = {}
  for _, path in ipairs(SHELL_TOML) do
    local text = read(path)
    if text then
      local section = ""
      for line in text:gmatch("[^\n]+") do
        local s = line:match("^%s*%[%s*([%w_.-]+)%s*%]")
        if s then
          section = s
        else
          local k, v = line:match("^%s*([%w_.-]+)%s*=%s*(.-)%s*$")
          if k and v then
            v = v:gsub("%s+#.*$", "")
            v = v:gsub('^"(.*)"$', "%1")
            values[section .. "." .. k] = v
          end
        end
      end
    end
  end
  return values
end

-- the dock body's depth (gap + icon slot) and the whole dock layer's height, both in logical px
function M.dock_metrics(values)
  values = values or shell_values()
  local base = tonumber(values["font.base-size"] or "")
  base = base and math.floor(base) or 12
  if base < 1 then base = 1 end
  local font = math.max(1 / 12, base / 12)
  local scale = tonumber(values["spacing.scale"] or "") or 1
  if scale < 0 then scale = 1 end
  local with_font = (values["spacing.scale-with-font"] or "true"):lower()
  with_font = not (with_font == "false" or with_font == "0" or with_font == "no" or with_font == "off")
  local spacing = scale * (with_font and font or 1)
  local function space(px)
    local n = px * spacing
    if n <= 0 then return 0 end
    return math.max(1, round(n))
  end
  local function token(key, px)
    local v = tonumber(values["spacing." .. key] or "")
    if v and v >= 0 then return round(v) end
    return space(px)
  end
  local border = tonumber(values["controls.normal-border-width"] or values["style.normal-border-width"] or "") or 1
  border = math.max(0, round(border))
  local gap = token("xs", 3)
  local slot = round(36 * font) + 2 * token("md", 6)
  local popup = token("popup-row-height", 28) * 5 + token("sm", 4) * 2 + border * 2 + gap * 2
  return gap + slot, gap + slot + popup
end

-- the live omarchy-dock layer on this monitor: x, y, w, h (logical, global) or nil
local function dock_layer(monitor)
  local ok, layers = pcall(hl.get_layers)
  if not ok or type(layers) ~= "table" then
    return nil
  end
  for _, layer in ipairs(layers) do
    if layer.namespace == "omarchy-dock" and (layer.h or 0) > 0 and (layer.w or 0) > 0 then
      local lm = layer.monitor
      if not lm or not monitor or lm.name == nil or lm.name == monitor.name then
        return layer
      end
    end
  end
  return nil
end

-- which edge the dock is on and how deep its body is there
function M.dock_room(monitor, values)
  local depth, layer_h = M.dock_metrics(values)
  local layer = dock_layer(monitor)
  local edge = "bottom"
  if layer then
    local vertical = layer.h > layer.w
    local thick = vertical and layer.w or layer.h
    if thick ~= layer_h and layer_h > 0 then
      -- a shell value this file does not know about: keep the body's share of the real layer
      depth = round(thick * depth / layer_h)
    end
    if vertical then
      edge = ((layer.x or 0) <= (monitor and monitor.x or 0) + 1) and "left" or "right"
    elseif (layer.y or 0) <= (monitor and monitor.y or 0) + 1 and layer.h < 300 then
      edge = "top"
    end
  end
  depth = math.max(16, math.min(240, depth))
  return edge, depth
end

-- ---- the titlebar ----

local titlebar_height = nil   -- what this file set for plugin.hyprbars.bar_height (tablet mode), nil = not set

local function titlebars_loaded()
  local ok, loaded = pcall(function() return hl.plugin ~= nil and hl.plugin.hyprbars ~= nil end)
  return ok and loaded
end

function M.titlebar_for_scale(scale)
  scale = tonumber(scale) or 2
  if scale <= 0 then scale = 2 end
  return math.max(TITLEBAR_MIN, math.min(TITLEBAR_MAX, math.ceil(TITLEBAR_PX / scale)))
end

local function titlebar(window)
  if not titlebars_loaded() or not has_tag(window, WORKSPACE_TAG) then
    return 0
  end
  if titlebar_height then
    return titlebar_height
  end
  local ok, v = pcall(hl.get_config, "plugin.hyprbars.bar_height")
  v = ok and tonumber(type(v) == "table" and (v.int or v.value) or v) or nil
  return v or TITLEBAR_MIN
end

-- ---- the fit ----

-- the box (global logical px, without the titlebar above it) a fitted window gets on its monitor
function M.target(window, values)
  local monitor = window.monitor
  if not monitor or not monitor.width or not monitor.scale or monitor.scale <= 0 then
    return nil
  end
  local width = math.floor(monitor.width / monitor.scale)
  local height = math.floor(monitor.height / monitor.scale)
  if (monitor.transform or 0) % 2 == 1 then
    width, height = height, width
  end
  local r = monitor.reserved or {}
  local top, left, right, bottom = r.top or 0, r.left or 0, r.right or 0, r.bottom or 0
  if bottom >= OSK_MIN then
    bottom = 0   -- floatkey's docked keyboard: transient, the fit must not follow it
  end
  -- the dock body's depth already holds its own gap to the screen edge; GAP is kept between it and the window
  local edge, depth = M.dock_room(monitor, values)
  local room = { top = 0, left = 0, right = 0, bottom = 0 }
  room[edge] = depth
  local bar = titlebar(window)
  local x = (monitor.x or 0) + left + room.left + GAP
  local y = (monitor.y or 0) + top + room.top + GAP + bar
  local w = width - left - right - room.left - room.right - 2 * GAP
  local h = height - top - bottom - room.top - room.bottom - 2 * GAP - bar
  if w < 100 or h < 100 then
    return nil
  end
  return { x = math.floor(x), y = math.floor(y), w = math.floor(w), h = math.floor(h),
           mw = math.floor(width), mh = math.floor(height), bar = bar, edge = edge, depth = depth }
end

local RECORD_PATTERN = "^iceland%-fit%-(%-?%d+)_(%-?%d+)_(%d+)x(%d+)_(%d+)x(%d+)%*?$"

local function record_of(window)
  for _, t in ipairs(window.tags or {}) do
    local x, y, w, h, mw, mh = t:match(RECORD_PATTERN)
    if x then
      local tag = t:gsub("%*$", "")
      return { x = tonumber(x), y = tonumber(y), w = tonumber(w), h = tonumber(h), mw = tonumber(mw),
               mh = tonumber(mh), tag = tag }
    end
  end
  return nil
end

local function near(a, b)
  return a and b and math.abs(a - b) <= TOLERANCE
end

local function geometry(window)
  local at, size = window.at or {}, window.size or {}
  return at.x, at.y, size.x, size.y
end

local function fittable(window)
  return window and window.floating and (window.fullscreen or 0) == 0 and not window.pinned
end

local function drop_fit(window)
  local rec = record_of(window)
  if rec then
    hl.dispatch(hl.dsp.window.tag({ tag = "-" .. rec.tag, window = window }))
  end
  hl.dispatch(hl.dsp.window.tag({ tag = "-" .. FIT_TAG, window = window }))
end

-- how: "force" (a new window, a mode change), "check" (a reload, a layer surface came or went, a modeset: the
-- window must still have the size AND position of our last fit). On a monitor whose logical size changed since that
-- fit (rotation, scale) Hyprland may have moved the window, so only its size must still be ours there, and a window
-- that no longer fits the new area is fitted in any case.
function M.fit(window, how)
  if not fittable(window) then
    return false
  end
  local t = M.target(window)
  if not t then
    return false
  end
  local x, y, w, h = geometry(window)
  if how ~= "force" then
    local rec = record_of(window)
    if rec then
      local turned = rec.mw ~= t.mw or rec.mh ~= t.mh
      local ours = near(w, rec.w) and near(h, rec.h) and (turned or (near(x, rec.x) and near(y, rec.y)))
      local spills = turned and w and h and (w > t.w + TOLERANCE or h > t.h + TOLERANCE)
      if not ours and not spills then
        drop_fit(window)   -- the owner moved / resized it: never touched again until the next mode change
        return false
      end
    end
  end
  if not (w == t.w and h == t.h) then
    hl.dispatch(hl.dsp.window.resize({ x = t.w, y = t.h, relative = false, window = window }))
  end
  if not (x == t.x and y == t.y) then
    hl.dispatch(hl.dsp.window.move({ x = t.x, y = t.y, relative = false, window = window }))
  end
  local rec = record_of(window)
  local tag = string.format("%s%d_%d_%dx%d_%dx%d", RECORD, t.x, t.y, t.w, t.h, t.mw, t.mh)
  if not rec or rec.tag ~= tag then
    if rec then
      hl.dispatch(hl.dsp.window.tag({ tag = "-" .. rec.tag, window = window }))
    end
    hl.dispatch(hl.dsp.window.tag({ tag = "+" .. tag, window = window }))
  end
  if not has_tag(window, FIT_TAG) then
    hl.dispatch(hl.dsp.window.tag({ tag = "+" .. FIT_TAG, window = window }))
  end
  return true
end

function M.refit(tags, how)
  if not tablet() then
    return 0
  end
  local seen, n = {}, 0
  for _, tag in ipairs(tags) do
    for _, window in ipairs(hl.get_windows({ tag = tag })) do
      if not seen[window.address] then
        seen[window.address] = true
        if M.fit(window, how) then n = n + 1 end
      end
    end
  end
  return n
end

-- one refit per burst of events (a modeset fires several, a keyboard show / hide two layer changes)
local pending = 0
local function later(how, ms)
  pending = pending + 1
  local mine = pending
  hl.timer(function()
    if mine == pending then
      M.refit({ FIT_TAG }, how)
    end
  end, { type = "oneshot", timeout = ms })
end

-- a new window Omarchy's floating-workspace rule opened (after Omarchy's own handler, which runs first)
hl.on("window.open", function(window)
  if tablet() and has_tag(window, OPENED_TAG) then
    hl.timer(function() M.fit(window, "force") end, { type = "oneshot", timeout = 1 })
  end
end)

-- a rotation (iceland-rotate), a scale or refresh modeset changes the monitor: refit the windows we fitted
hl.on("monitor.layout_changed", function()
  later("check", 250)
end)

-- the dock, the bar or the keyboard came or went (the reserved area may have changed): refit what is still ours
local function layer_changed(layer)
  local ns = layer and layer.namespace or ""
  if ns == "omarchy-dock" or ns == "omarchy-bar" or ns == "floatkey" or ns:match("^omarchy%-pad") then
    later("check", 300)
  end
end
hl.on("layer.opened", layer_changed)
hl.on("layer.closed", layer_changed)

-- the titlebar: finger sized in tablet mode (Omarchy's titlebars() set its own 30 earlier in this config pass;
-- iceland.lua runs last). Only while the plugin is loaded: an unknown key would abort this file.
if tablet() and titlebars_loaded() then
  local scale = 2
  local okm, mon = pcall(hl.get_active_monitor)
  if okm and type(mon) == "table" and tonumber(mon.scale) then
    scale = mon.scale
  end
  local h = M.titlebar_for_scale(scale)
  if pcall(hl.config, { plugin = { hyprbars = { bar_height = h } } }) then
    titlebar_height = h
  end
end

-- the reload right after a mode change (iceland-tablet-layout leaves the marker): every window Omarchy just floated
-- for tablet mode fills the screen; an ordinary reload (theme change, ...) keeps the sizes the owner chose
local marker = io.open(REFIT, "r")
if marker then
  marker:close()
  os.remove(REFIT)
  hl.timer(function() M.refit({ FLOATED_TAG, FIT_TAG }, "force") end, { type = "oneshot", timeout = 300 })
end

-- an ordinary reload: our windows are checked once (a -18 fit squeezed by the keyboard grows back)
if not marker then
  hl.timer(function() M.refit({ FIT_TAG }, "check") end, { type = "oneshot", timeout = 400 })
end

if rawget(_G, "ICELAND_TABLET_TEST") then
  ICELAND_TABLET_TEST.M = M
end
