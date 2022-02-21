#spyu_model.py
# interface to attach spyu db to connection (listoffers in memory db)
import sqlite3

import debug

_schema_version = 4
from ..get_datadir import get_datadir

def _attach_dummy_spyu(con):
    """ create a dummy ie empty in memory replacement for spyu """
    con.execute(f"ATTACH ':memory:' AS spyu")
    con.executescript("""
CREATE TABLE spyu.provider (providerId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, addr TEXT NOT NULL UNIQUE);
CREATE TABLE spyu.nodeInfo (nodeInfoId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, providerId REFERENCES provider(providerId), modelname TEXT DEFAULT '', unixtime DECIMAL NOT NULL, nodename TEXT NOT NULL);
CREATE TABLE spyu.schema_version(version INT NOT NULL);
    """)

def attach_spyu(con):
    """ attach real or empty in memory spyu """
    spyu_db_po = get_datadir() / "gc_spyu" / "gc_spyu.db"
    dbpath_as_uri=f"file:{spyu_db_po}?mode=ro"
    debug.dlog("----------- attaching spyu ------------")
    try:
        con.execute(f"ATTACH '{dbpath_as_uri}' AS spyu")
    except sqlite3.OperationalError:
        _attach_dummy_spyu(con)
        con.execute("INSERT INTO spyu.schema_version(version) VALUES (?)"
                , [ 0 ])
    rs = con.execute("SELECT version FROM spyu.schema_version")
    debug.dlog(f"spyu schema version: {next(rs)[0]}")
