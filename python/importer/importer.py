#!/usr/bin/python
import os, sys
import sqlite3 as sqlite
import imdict, trie
from pinyin_data import valid_syllables, decode_syllable

def get_userdict_path ():
    homedir = os.environ.get("HOME")

    if sys.platform == "darwin":
        return homedir+"/Library/Application Support/SunPinyin/userdict"

    # FIXME: not sure how to get the ibus version or wrapper type (xim or ibus)
    if os.path.exists (homedir+"/.cache/ibus/sunpinyin"):
        return homedir+"/.cache/ibus/sunpinyin/userdict"
    
    if os.path.exists (homedir+"/.sunpinyin"):
        return homedir+"/.sunpinyin/userdict"

    raise "Can not detect sunpinyin's userdict!"

def import_to_sunpinyin_user_dict (records, userdict_path=''):
    userdict_path = userdict_path if userdict_path else get_userdict_path()
    db = sqlite.connect (userdict_path)

    sysdict = imdict.IMDict("dict.utf8")

    sqlstring = """
            CREATE TABLE IF NOT EXISTS dict(
            id INTEGER PRIMARY KEY, len INTEGER,
            i0 INTEGER, i1 INTEGER, i2 INTEGER, i3 INTEGER, i4 INTEGER, i5 INTEGER,
            f0 INTEGER, f1 INTEGER, f2 INTEGER, f3 INTEGER, f4 INTEGER, f5 INTEGER,
            utf8str TEXT, UNIQUE (utf8str));
            """
    db.executescript (sqlstring)

    for (pystr, utf8str) in records:
        syllables = [valid_syllables[s] for s in pystr.split("'")]
        if len (syllables) < 2 or len (syllables) > 6:
            #print "[%s] is too long or too short for sunpinyin userdict" % utf8str
            continue;

        if sysdict and trie.search (sysdict, utf8str):
            #print "[%s] is already in sunpinyin's sysdict" % utf8str
            continue

        record = [0]*14
        record[0] = len (syllables)
        record[13] = utf8str

        c = 1
        for s in syllables:
            i, f = s>>12, (s&0x00ff0)>>4
            if i and not f:
                break; 
            record[c] = i
            record[c+1] = f
            c += 2
        else:
            sqlstring = """
                    INSERT INTO dict (len, i0, f0, i1, f1, i2, f2, i3, f3, i4, f4, i5, f5, utf8str)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """
            try:
                db.execute (sqlstring, record)
                db.commit ()
                print "[%s] is imported into sunpinyin's userdict" % utf8str
            except:
                #print "[%s] is already in sunpinyin's userdict" % utf8str
                pass

    db.close()
