# -*- coding: utf-8 -*-
import sys
from bs4 import BeautifulSoup
import codecs
import re
import argparse
import logging
import glob
import os
import sqlite3
from sqlite3.dbapi2 import Error

# Import common scripts
CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CWD)
sys.path.insert(0, os.path.normpath(os.path.join(CWD, '..', '..')))

import shmaplib

# Import common shortcut mapper library
log = shmaplib.setuplog(os.path.join(CWD, 'output.log'))

def main():
    parser = argparse.ArgumentParser(
        description="Converts Database files to an intermediate format.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        required=False, help="Verbose output")
    parser.add_argument('-o', '--output', required=True,
                        help="Output filepath")
    parser.add_argument(
        'source', help="Source: Database (.db, .sql) containing shortcuts (/raw folder)")

    args = parser.parse_args()
    args.source = os.path.abspath(args.source)
    args.output = os.path.abspath(args.output)

    if not os.path.exists(args.source):
        print("Error: the input source file doesn't exist.")
        return

    # Verbosity setting on log
    log.setLevel(logging.INFO)
    if args.verbose:
        log.setLevel(logging.DEBUG)

    conn = sqlite3.connect(args.source)

    curs = conn.cursor()

    query = "SELECT value FROM about WHERE property is ?;"

    props = (
        curs.execute(query, ('name',)).fetchone()[0],
        curs.execute(query, ('version',)).fetchone()[0],
        curs.execute(query, ('default_context',)).fetchone()[0],
        [plat[0] for plat in curs.execute(query, ('os',)).fetchall()]
    )
    print(props[3])

    iData = shmaplib.IntermediateShortcutData(*props)

    query = "SELECT name FROM sqlite_master WHERE type='view';"

    views = (table[0] for table in curs.execute(query).fetchall())

    for view in views:
        query = "SELECT * FROM %s"
        keybinds = curs.execute(query % view).fetchall()
        for keybind in keybinds:
            context_name, label, keys_win, keys_mac = (
                view, keybind[0].title(), keybind[1], keybind[1]
            )
            if label == 'Ship-to-ship comlink':
                print(keys_win)
            # if 'Ctrl' in keys_mac:
            #     keys_mac = keys_mac + " / " + keys_mac.replace('Ctrl', 'Cmd')

            iData.add_shortcut(
                context_name, label, keys_win, keys_mac
            )

    output = os.path.join(args.output, iData.name) + '.json'
    iData.serialize(output)

    conn.close()


if __name__ == '__main__':
    main()
