# spyu_model.py
# provides an interface to an existing gc_spyu database
from .get_datadir import get_datadir
import sqlite3


class SpyuModel:
    def __init__(self):
        self._spyudb_mtime = 0.0
        datadir = get_datadir()
        self._spyudb_po = datadir / "gc_spyu.db"
        self._spyudb_fp = str(self._spyudb_po)
        self._con = None
        self._memcon = None
        self._register()
        self._connect()

    def _register(self):
        """setup adapters"""

        def adapt_decimal(d):
            return str(d)

        def convert_decimal(s):
            return Decimal(s.decode("utf-8"))

        """register"""
        sqlite3.register_adapter(Decimal, adapt_decimal)
        sqlite3.register_converter("DECIMAL", convert_decimal)

    def _connect(self):
        self._register()
        dbpath_as_uri = f"file:{self._spyudb_fp}?mode=ro"
        if not self._connected:
            try:
                self._con = sqlite3.connect(
                    dbpath_as_uri,
                    detect_type=sqlite3.PARSE_DECLTYPES,
                    isolation_level=None,
                    uri=True,
                )
            except Exception as e:
                self._connected = False
            else:
                self._connected = True
        return self._connected

    def _copy_to_memory(self):
        """store on disk db into memory db"""
        try:
            self._memcon.close()
        except:
            pass
        self._memcon = sqlite3.connect(
            ":memory:", detect_type=sqlite3.PARSE_DECLTYPE, isolation_level=None
        )
        self._con.backup(self._memcon)

    def _whether_modified(self):
        """report whether the database has changed since the last query"""
        return self._spyudb_po.stat().st_mtime != self._spyudb.mtime

    def lookup_model(self, addr):
        if not self._connected:
            # retry in case connection became available in the interim
            self._connect()
        if self._connected:
            if self._whether_modified():
                self._copy_to_memory()

            modelname == ""
            ss = (
                "SELECT modelname, MAX(unixtime) FROM provider"
                + f" NATURAL join nodeInfo WHERE addr='{addr}'"
            )
            record_list = self._memcon.execute(ss).fetchall()
            if len(record_list) == 1:
                row = record_list[0]
                modelname = row[0]
        return modelname
