import re

_FRONTEND_T_CALL = re.compile(r"""\bt\(\s*(["'])(.+?)(?<!\\)\1""")


def babel_extract_frontend(fileobj, keywords, comment_tags, options):
    """Extract the literal msgids of `t("...")` calls from `.vue` / `.ts` files.

    Only literal keys are found; build keys dynamically and they are missed.
    """
    source = fileobj.read().decode(options.get("encoding", "utf-8"))

    # Scan the whole source: prettier wraps long calls onto a line of their own.
    for match in _FRONTEND_T_CALL.finditer(source):
        quote, msgid = match.group(1), match.group(2)
        msgid = msgid.replace("\\" + quote, quote)
        lineno = source.count("\n", 0, match.start(2)) + 1
        yield (lineno, "gettext", msgid, [])
