"""Central visual design tokens for Mentor.

The values are mutable at runtime so Appearance settings can be applied without
restarting the application.  Widgets that bake colors into custom styles are
recreated by MainWindow after preferences change.
"""

BG = "#060607"
BG2 = "#09090A"
BG3 = "#0C0C0E"
SURFACE = "#111113"
SURFACE2 = "#161618"
SURFACE3 = "#1B1B1E"
HOVER = "#202024"
PRESSED = "#252529"
TEXT = "#F5F5F7"
TEXT2 = "#B0B0B6"
MUTED = "#74747C"
SUCCESS = "#63D197"
WARNING = "#E6A34A"
ERROR = "#E26D6D"
INFO = "#8EA9FF"
BORDER = "rgba(255,255,255,22)"
BORDER_HOVER = "rgba(255,255,255,35)"
BORDER_SUBTLE = "rgba(255,255,255,12)"
RADIUS_CARD = 22
RADIUS_SMALL = 12
RADIUS_PILL = 999
SPACE_XS = 6
SPACE_SM = 10
SPACE_MD = 16
SPACE_LG = 24
SPACE_XL = 32

ACCENT_PRESETS = {
    "orange": ("#FF8A2A", "#FFA04D", "#FF6A00", "#2A190F"),
    "amber": ("#F5A524", "#FFC052", "#DB8710", "#2A210F"),
    "graphite": ("#B7B7BE", "#D4D4D8", "#8F8F98", "#202023"),
    "blue": ("#5B9DFF", "#82B5FF", "#367FEA", "#111D2C"),
    "violet": ("#9B7BFF", "#B59CFF", "#7C5AE6", "#1D172C"),
}
ACCENT_KEY = "orange"
ACCENT, ACCENT_BRIGHT, ACCENT_DARK, ACCENT_SOFT = ACCENT_PRESETS[ACCENT_KEY]
DENSITY = "comfortable"
GLASS = "standard"
MOTION = "full"
AMBIENT_GLOW = True
ANIM_FAST = 140
ANIM_NORMAL = 210
ANIM_PAGE = 230


def apply_preferences(*, accent: str = "orange", density: str = "comfortable", glass: str = "standard", motion: str = "full", ambient_glow: bool = True) -> None:
    global ACCENT_KEY, ACCENT, ACCENT_BRIGHT, ACCENT_DARK, ACCENT_SOFT
    global DENSITY, GLASS, MOTION, AMBIENT_GLOW, ANIM_FAST, ANIM_NORMAL, ANIM_PAGE
    ACCENT_KEY = accent if accent in ACCENT_PRESETS else "orange"
    ACCENT, ACCENT_BRIGHT, ACCENT_DARK, ACCENT_SOFT = ACCENT_PRESETS[ACCENT_KEY]
    DENSITY = density if density in {"comfortable", "compact"} else "comfortable"
    GLASS = glass if glass in {"subtle", "standard", "strong"} else "standard"
    MOTION = motion if motion in {"full", "reduced", "off"} else "full"
    AMBIENT_GLOW = bool(ambient_glow)
    if MOTION == "off":
        ANIM_FAST = ANIM_NORMAL = ANIM_PAGE = 0
    elif MOTION == "reduced":
        ANIM_FAST, ANIM_NORMAL, ANIM_PAGE = 80, 110, 120
    else:
        ANIM_FAST, ANIM_NORMAL, ANIM_PAGE = 140, 210, 230


def glass_alpha() -> int:
    return {"subtle": 252, "standard": 246, "strong": 226}.get(GLASS, 246)


def control_vpad() -> int:
    return 6 if DENSITY == "compact" else 9


def button_vpad() -> int:
    return 6 if DENSITY == "compact" else 8