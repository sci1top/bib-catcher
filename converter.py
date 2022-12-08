# %%
import re
import pandas as pd
import os
import argparse
from gscholar import query
import bibtexparser
import pyperclip as pc
import json

from utils import *
from obsidian import write_note

from functools import partial

# %%

parser = argparse.ArgumentParser()
parser.add_argument('citekey', type=str, default="", nargs='?')
args = parser.parse_args()

CITEKEY = args.citekey.lstrip('@')
if CITEKEY == "":
    with open(os.path.join(base_dir, 'history.txt'), 'r') as f:
        CITEKEY = f.readlines()[-1]
        cprint(f"[INFO] Load recent paper: {CITEKEY}")

# %%

df = pd.read_csv(os.path.join('output', CITEKEY, 'title.csv'))

if os.path.exists(zotero_bib_path):
    with open(zotero_bib_path, "r") as f:
        zdf = pd.DataFrame(bibtexparser.load(f).entries)
else:
    zdf = None

ob_config_path = os.path.join(obsidian_bse_path, ob_citation_plugin_path)
if os.path.exists(ob_config_path):
    with open(ob_config_path, 'r') as f:
        ob_template = json.loads(f.read())['literatureNoteContentTemplate']
else:
    ob_template = None

citekey_to_touch = []


def touch_note(citekey):
    # print("touch", citekey)
    if ob_template is None:
        cprint("no template", 31)
        return
    note_path = os.path.join(obsidian_bse_path, ob_note_path, f"@{citekey}.md")
    # print(note_path)
    if os.path.exists(note_path):
        cprint(f"[INFO] Note exists: {citekey}")
        return
    md = write_note(citekey, ob_template, zdf)
    if md == "":
        return
    cprint(f"[INFO] Write new note: {citekey}", 33)
    with open(note_path, 'w') as f:
        f.write(md)


def idx2citekey(idx):
    cdf = df[df.cidx == int(idx)]
    if len(cdf) == 0:
        return ""
    else:
        citekey = cdf.citekey.tolist()[0]
        return citekey


def note_idx2citekey(r):
    content = ""
    idxs = r.group(2).strip('[]').split(',')
    for idx in idxs:
        cdf = df[df.cidx == int(idx)]
        if content != "":  # not the first one
            content += ", "

        if len(cdf) == 0:
            content += idx
        else:
            citekey = cdf.citekey.tolist()[0]
            content += f"[[@{citekey}]]"
            citekey_to_touch.append(citekey)

    if len(idxs) == 1 and zdf is not None:
        bdf = zdf[zdf.ID == citekey]
        if len(bdf) != 0:
            if pd.notna(bdf.shorttitle.tolist()[0]):
                shorttitle = re.sub('[{}]', '', bdf.shorttitle.tolist()[0])
                if is_same_item(shorttitle, r.group(1)):
                    return f"[[{citekey}|{shorttitle}]]"

    return r.group(1) + " (" + content + ")"


# %%

if __name__ == '__main__':
    while True:
        try:
            cprint("[INFO] Input text: (Double enter to start conversion)")
            lines = [line for line in iter(partial(input, '>'), '')]
            text = '\n'.join(lines)

            if re.match(r'\d+', text) is not None:
                citekey = idx2citekey(int(text))
                cprint(f"{citekey}: zotero://select/items/@{citekey}", 36)
            else:
                cprint("Result:", 44)
                output = re.sub(r'([\w\.]+) (\[[\d,]+\])', note_idx2citekey,
                                text)
                pc.copy(output)
                cprint(output, 36)
                print()

                cprint(
                    "[INFO] The content has been replaced in the clipboard!")
                for ck in citekey_to_touch:
                    touch_note(ck)
                citekey_to_touch = []
                print("==" * 30)
        except KeyboardInterrupt:
            print("Bye~")
            break