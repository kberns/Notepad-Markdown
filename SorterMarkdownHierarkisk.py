
# -*- coding: utf-8 -*-
from Npp import editor, notepad
import re

# Innstillinger
SORTER_HOVEDOVERSKRIFTER = True
SORTER_UNDEROVERSKRIFTER = True

# Hent tekst
original = editor.getText()
was_bytes = isinstance(original, bytes)

if was_bytes:
    text = original.decode("utf-8")
else:
    text = original

lines = text.splitlines(True)

# Markdown-overskrift: # til ######
heading_re = re.compile(
    r'^[ ]{0,3}(#{1,6})(?:[ \t]+|$)([^\r\n]*)'
)

# Fenced code blocks
fence_re = re.compile(
    r'^[ ]{0,3}(`{3,}|~{3,})([^\r\n]*)'
)

# Roten inneholder tekst før første overskrift
def new_node(level, title=u""):
    return {
        "level": level,
        "title": title,
        "lines": [],
        "children": []
    }

root = new_node(0)
stack = [root]

fence_char = None
fence_size = 0

for line in lines:

    # Finn åpning/lukking av kodeblokk
    fence = fence_re.match(line)

    if fence:
        marker = fence.group(1)
        suffix = fence.group(2)
        char = marker[0]

        if fence_char is None:
            # Åpning
            if char == '~' or '`' not in suffix:
                fence_char = char
                fence_size = len(marker)
        else:
            # Lukking
            if (char == fence_char and
                len(marker) >= fence_size and
                not suffix.strip()):
                fence_char = None
                fence_size = 0

        stack[-1]["lines"].append(line)
        continue

    # Overskrifter inne i kodeblokker ignoreres
    if fence_char is not None:
        stack[-1]["lines"].append(line)
        continue

    match = heading_re.match(line)

    if match:
        level = len(match.group(1))

        title = match.group(2).strip()

        # Fjern avsluttende Markdown-hash
        title = re.sub(
            r'[ \t]+#+[ \t]*$',
            '',
            title
        ).strip()

        # Finn riktig overordnet overskrift
        while stack[-1]["level"] >= level:
            stack.pop()

        node = new_node(level, title)
        node["lines"].append(line)

        stack[-1]["children"].append(node)
        stack.append(node)

    else:
        stack[-1]["lines"].append(line)


# Norsk alfabetisk rekkefølge
def sort_key(node):
    title = node["title"].lower()

    # Æ, Ø og Å skal etter Z
    title = title.replace(u'æ', u'{')
    title = title.replace(u'ø', u'|')
    title = title.replace(u'å', u'}')

    return title


# Sorter rekursivt
def sort_node(node):

    for child in node["children"]:
        sort_node(child)

    if node["level"] == 0:
        if SORTER_HOVEDOVERSKRIFTER:
            node["children"].sort(key=sort_key)
    else:
        if SORTER_UNDEROVERSKRIFTER:
            node["children"].sort(key=sort_key)


# Bygg dokumentet på nytt
def render(node):
    result = u''.join(node["lines"])

    for child in node["children"]:
        result += render(child)

    return result


# Tell overskrifter
def count_nodes(node):
    total = len(node["children"])

    for child in node["children"]:
        total += count_nodes(child)

    return total


count = count_nodes(root)

if count < 2:
    notepad.messageBox(
        "Fant færre enn to overskrifter.",
        "Markdown sortering"
    )
else:
    sort_node(root)
    result = render(root)

    if result != text:

        if was_bytes:
            result = result.encode("utf-8")

        editor.beginUndoAction()

        try:
            editor.setText(result)
        finally:
            editor.endUndoAction()

        notepad.messageBox(
            "%d overskrifter behandlet." % count,
            "Markdown sortering fullført"
        )

    else:
        notepad.messageBox(
            "Dokumentet er allerede sortert.",
            "Markdown sortering"
        )
# @copyright    Creative Commons Attribution 4.0 International (CC BY 4.0) 
# @source https://github.com/krizoek/Notepad-Markdown
# @author Kristoffer Bernssen
