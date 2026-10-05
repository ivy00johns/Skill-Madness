"""Conservative source extraction, not a CSS/JS compiler or a render verifier."""
import hashlib
import re


def mask_comments(text):
    # Preserve quoted strings and newlines while removing CSS/JS/HTML comments.
    pattern = re.compile(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|(/\*.*?\*/|<!--.*?-->|//[^\n]*)''', re.S)
    return pattern.sub(lambda m: m.group(1) or re.sub(r"[^\n]", " ", m.group(2)), text)


def compact(text):
    # Never alter whitespace inside quoted values (content, URLs, attribute data).
    parts = re.split(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')''', text)
    return "".join(part if i % 2 else re.sub(r"\s+", " ", part)
                   for i, part in enumerate(parts)).strip()


def css_blocks(text):
    """Yield flat declaration blocks with full at-rule ancestry and positions.

    Nesting, preprocessors, selector lists and complex selectors are not merged.
    Exact declarations retain order: fallback/duplicate properties are semantic.
    """
    text = mask_comments(text)

    def walk(start, end, scope):
        cursor = start
        i = start
        quote = None
        parens = 0
        while i < end:
            c = text[i]
            if quote:
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    quote = None
            elif c in "\"'":
                quote = c
            elif c == "(":
                parens += 1
            elif c == ")":
                parens -= 1
            elif not parens and c == ";":
                cursor = i + 1
            elif not parens and c == "{":
                header = text[cursor:i].strip()
                depth, j, inner_quote = 1, i + 1, None
                while j < end and depth:
                    ch = text[j]
                    if inner_quote:
                        if ch == "\\":
                            j += 2
                            continue
                        if ch == inner_quote:
                            inner_quote = None
                    elif ch in "\"'":
                        inner_quote = ch
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                    j += 1
                if depth:
                    raise ValueError("unbalanced CSS block")
                body = text[i + 1:j - 1]
                if header.startswith("@"):
                    yield from walk(i + 1, j - 1, scope + (compact(header),))
                elif "{" not in body:
                    yield header, body, scope, cursor
                i = j
                cursor = j
                continue
            i += 1
    yield from walk(0, len(text), ())


def declaration_key(body):
    # Split only outside strings/functions; data URLs may contain semicolons.
    pieces, start, quote, depth = [], 0, None, 0
    i = 0
    while i < len(body):
        c = body[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == ";" and not depth:
            pieces.append(body[start:i])
            start = i + 1
        i += 1
    pieces.append(body[start:])
    declarations = []
    for piece in pieces:
        if not piece.strip():
            continue
        if ":" not in piece:
            return ()
        name, value = piece.split(":", 1)
        name = name.strip()
        if not re.fullmatch(r"(?:--)?[\w-]+", name):
            return ()
        # Normalize token separators outside quoted strings without reordering
        # declarations or erasing required whitespace in compound values.
        value = compact(value)
        parts = re.split(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')''', value)
        value = "".join(part if i % 2 else re.sub(r"\s*([,()])\s*", r"\1", part)
                        for i, part in enumerate(parts))
        declarations.append((name if name.startswith("--") else name.lower(), value))
    return tuple(declarations)


def fingerprint(value):
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def chrome_blocks(text, tags):
    """Extract literal semantic chrome, preserving content/attributes/variants."""
    text = mask_comments(text)
    # Script literals are not authored DOM; style content is also not markup.
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>",
                  lambda m: re.sub(r"[^\n]", " ", m.group()), text, flags=re.S | re.I)
    tokens = re.compile(r'''<(/?)([A-Za-z][\w:-]*)\b(?:"[^"]*"|'[^']*'|[^'">])*?>''', re.S)
    stack = []
    for match in tokens.finditer(text):
        name = match.group(2).lower()
        if name not in tags:
            continue
        if match.group(1):
            if stack and stack[-1][0] == name:
                _, start = stack.pop()
                block = text[start:match.end()]
                normalized = re.sub(r">\s+<", "><", compact(block))
                yield name, normalized, text.count("\n", 0, start) + 1
        elif not match.group().endswith("/>"):
            stack.append((name, match.start()))
