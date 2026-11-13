#!/usr/bin/env python3
"""Convert HTML markup into real, editable JSX.

Not a string wrapper: this walks the DOM and emits JSX source, mapping
attributes (class -> className, style string -> style object, SVG
hyphenated props -> camelCase) so the output is ordinary React you can
edit by hand.
"""
import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

# HTML/SVG attribute -> JSX prop. Anything data-*/aria-* passes through.
ATTR_MAP = {
    "class": "className", "for": "htmlFor", "tabindex": "tabIndex",
    "colspan": "colSpan", "rowspan": "rowSpan", "maxlength": "maxLength",
    "minlength": "minLength", "readonly": "readOnly", "contenteditable":
    "contentEditable", "spellcheck": "spellCheck", "autocomplete":
    "autoComplete", "autofocus": "autoFocus", "autoplay": "autoPlay",
    "playsinline": "playsInline", "crossorigin": "crossOrigin",
    "fetchpriority": "fetchPriority", "srcset": "srcSet", "usemap": "useMap",
    "novalidate": "noValidate", "enctype": "encType", "formaction":
    "formAction", "accept-charset": "acceptCharset", "http-equiv":
    "httpEquiv", "datetime": "dateTime", "frameborder": "frameBorder",
    "allowfullscreen": "allowFullScreen", "marginwidth": "marginWidth",
    "marginheight": "marginHeight", "referrerpolicy": "referrerPolicy",
    # SVG
    "stroke-width": "strokeWidth", "stroke-linecap": "strokeLinecap",
    "stroke-linejoin": "strokeLinejoin", "stroke-dasharray":
    "strokeDasharray", "stroke-dashoffset": "strokeDashoffset",
    "stroke-opacity": "strokeOpacity", "stroke-miterlimit":
    "strokeMiterlimit", "fill-rule": "fillRule", "fill-opacity":
    "fillOpacity", "clip-path": "clipPath", "clip-rule": "clipRule",
    "stop-color": "stopColor", "stop-opacity": "stopOpacity",
    "flood-color": "floodColor", "flood-opacity": "floodOpacity",
    "gradientunits": "gradientUnits", "gradienttransform":
    "gradientTransform", "patternunits": "patternUnits",
    "patterncontentunits": "patternContentUnits", "preserveaspectratio":
    "preserveAspectRatio", "viewbox": "viewBox", "xlink:href": "xlinkHref",
    "xmlns:xlink": "xmlnsXlink", "text-anchor": "textAnchor",
    "dominant-baseline": "dominantBaseline", "font-family": "fontFamily",
    "font-size": "fontSize", "font-weight": "fontWeight", "letter-spacing":
    "letterSpacing", "color-interpolation-filters":
    "colorInterpolationFilters", "maskunits": "maskUnits", "masktype":
    "maskType", "filterunits": "filterUnits", "primitiveunits":
    "primitiveUnits", "baseprofile": "baseProfile", "shape-rendering":
    "shapeRendering", "vector-effect": "vectorEffect", "paint-order":
    "paintOrder",
}

# Attributes React wants as real booleans rather than strings.
BOOL_ATTRS = {"autoPlay", "playsInline", "muted", "loop", "controls",
              "disabled", "checked", "readOnly", "required", "autoFocus",
              "hidden", "noValidate", "allowFullScreen", "defer", "async",
              "selected", "multiple", "reversed", "open"}


def css_to_obj(style: str) -> str:
    """'a:b;c:d' -> "{{ a: 'b', c: 'd' }}" with JSX-safe keys."""
    parts = []
    for decl in style.split(";"):
        decl = decl.strip()
        if not decl or ":" not in decl:
            continue
        prop, _, val = decl.partition(":")
        prop, val = prop.strip(), val.strip()
        if not prop:
            continue
        if prop.startswith("--"):
            key = f"'{prop}'"                       # custom property
        else:
            head, *rest = prop.split("-")
            key = head + "".join(w.capitalize() for w in rest if w)
            if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", key):
                key = f"'{prop}'"
        parts.append(f"{key}: {js_str(val)}")
    return "{{ " + ", ".join(parts) + " }}" if parts else "{{}}"


def js_str(v: str) -> str:
    """Quote a value as a JS single-quoted string literal."""
    return "'" + v.replace("\\", "\\\\").replace("'", "\\'") \
                  .replace("\n", " ").replace("\r", "") + "'"


def jsx_text(t: str) -> str:
    """Escape raw text for a JSX child position."""
    return (t.replace("\\", "\\\\")
             .replace("{", "&#123;").replace("}", "&#125;")
             .replace("<", "&lt;").replace(">", "&gt;"))


class Html2Jsx(HTMLParser):
    def __init__(self, indent="      "):
        super().__init__(convert_charrefs=False)
        self.out = []
        self.base = indent
        self.depth = 0
        self.stack = []

    # -- helpers ---------------------------------------------------------
    def w(self, s):
        self.out.append(s)

    def pad(self):
        return self.base + "  " * self.depth

    def attrs_to_jsx(self, attrs, tag=""):
        parts = []
        for name, value in attrs:
            low = name.lower()
            if low.startswith("on"):          # drop inline event handlers
                continue
            # React wants the selected option expressed on the <select>, not
            # the <option>. The marked option here is always the leading
            # placeholder, which browsers select by default anyway.
            if tag == "option" and low == "selected":
                continue
            prop = ATTR_MAP.get(low, name if (
                low.startswith(("data-", "aria-"))) else ATTR_MAP.get(low, low))
            if low in ATTR_MAP:
                prop = ATTR_MAP[low]
            elif low.startswith(("data-", "aria-")):
                prop = name
            elif ":" in low or "-" in low:
                # unknown hyphenated/namespaced attr - keep verbatim, React
                # passes it through on DOM elements
                prop = name
            # React treats form value/checked as controlled state; the
            # mirror's markup is static, so use the uncontrolled variants.
            if tag in ("input", "textarea", "select"):
                if prop == "value":
                    prop = "defaultValue"
                elif prop == "checked":
                    prop = "defaultChecked"
            if value is None:
                # A valueless HTML attribute means "" - only real booleans
                # become {true}, otherwise React warns about non-booleans.
                parts.append(f"{prop}={{true}}" if prop in BOOL_ATTRS
                             else f'{prop}=""')
                continue
            if prop == "style":
                parts.append(f"style={css_to_obj(value)}")
            elif prop in BOOL_ATTRS:
                v = value.lower()
                parts.append(f"{prop}={{" + (
                    "false" if v in ("false", "0") else "true") + "}")
            else:
                parts.append(f"{prop}={js_str(value)}")
        return (" " + " ".join(parts)) if parts else ""

    # -- parser hooks ----------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = self.attrs_to_jsx(attrs, tag)
        if tag in VOID:
            self.w(f"{self.pad()}<{tag}{a} />\n")
        else:
            self.w(f"{self.pad()}<{tag}{a}>\n")
            self.stack.append(tag)
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.w(f"{self.pad()}<{tag}{self.attrs_to_jsx(attrs, tag)} />\n")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            # close any tags the source left open
            while self.stack and self.stack[-1] != tag:
                self.depth -= 1
                self.w(f"{self.pad()}</{self.stack.pop()}>\n")
            if self.stack:
                self.depth -= 1
                self.w(f"{self.pad()}</{self.stack.pop()}>\n")

    def handle_data(self, data):
        if not data:
            return
        stripped = data.strip()
        if not stripped:
            # Whitespace-only. Between block tags HTML collapses it away, but
            # a bare space between inline tags is real content - keep that.
            if "\n" not in data and " " in data:
                self.w(f"{self.pad()}{{' '}}\n")
            return
        lead = "{' '}" if data[:1] == " " else ""
        trail = "{' '}" if data[-1:] == " " else ""
        self.w(f"{self.pad()}{lead}{jsx_text(stripped)}{trail}\n")

    def handle_entityref(self, name):
        self.w(f"{self.pad()}&{name};\n")

    def handle_charref(self, name):
        self.w(f"{self.pad()}&#{name};\n")

    def handle_comment(self, data):
        pass                                    # drop HTML comments

    def close_all(self):
        while self.stack:
            self.depth -= 1
            self.w(f"{self.pad()}</{self.stack.pop()}>\n")
        super().close()


def convert(html: str, indent="      ") -> str:
    p = Html2Jsx(indent=indent)
    p.feed(html)
    p.close_all()
    return "".join(p.out)
