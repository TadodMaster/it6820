"""Final pass of the build: use a monospaced font for every text and label in the project."""
import re

FAMILY = "Monospaced"
# font of the label that a component shows (Text uses the attribute `font`, the others `labelfont`)
DEFAULTS = {"Text": "plain 12", "Tunnel": "bold 12", "Pin": "bold 12", "Probe": "plain 12", "Clock": "plain 12",
            "RAM": "plain 12", "ROM": "plain 12", "Register": "plain 11"}
NAMES = "|".join(DEFAULTS)

SELF_CLOSING = re.compile(r'<comp ((?:lib="\d+" )?loc="\([^)]*\)" )name="(' + NAMES + r')"/>')
OPEN = re.compile(r'<comp ((?:lib="\d+" )?loc="\([^)]*\)" )name="(' + NAMES + r')">(.*?)</comp>', re.S)


def monospace(text):
    """Returns the project text with every font changed to the monospaced family."""
    text = re.sub(r'val="(?:SansSerif|Dialog|Serif|Monospaced) ', f'val="{FAMILY} ', text)

    # a component written as <comp .../> gets an (empty) body so that the font attribute can be added
    text = SELF_CLOSING.sub(lambda m: f'<comp {m.group(1)}name="{m.group(2)}">\n    </comp>', text)

    def add_font(m):
        loc, name, body = m.group(1), m.group(2), m.group(3)
        key = "font" if name == "Text" else "labelfont"
        if f'name="{key}"' in body:
            return m.group(0)
        attr = f'\n      <a name="{key}" val="{FAMILY} {DEFAULTS[name]}"/>'
        return f'<comp {loc}name="{name}">{attr}{body}</comp>'

    return OPEN.sub(add_font, text)
