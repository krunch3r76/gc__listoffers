# sql.py
import sqlite3
import sys  # debug
import datetime
import itertools
import decimal
from decimal import Decimal
import json
import pprint

import debug
from .build_database_helpers import *
from ..get_datadir import get_datadir
from .spyu_model import *


# ++++++++++ create_database +++++++++++
def create_database():

    # _________ create_table_statement _________
    def _create_table_statement(tablename, cols_and_types):
        def substatement():
            # created a comma delimited list of each column description
            s = ""
            for col_and_type_s in cols_and_types:
                s += f"{col_and_type_s}, "
            s = s[:-2]
            return s

        statement = (
            f"create table '{tablename}' ( offerRowID INTEGER NOT NULL"
            f" REFERENCES offers(offerRowID), {substatement()}, extra TEXT"
            " DEFAULT '' )"
        )

        return statement

    # _____ adapt_decimal _______
    def adapt_decimal(d):
        return str(d)

    # _____ convert_decimal ______
    def convert_decimal(s):
        return Decimal(s.decode("utf-8"))

    # _____ grep_freq ______
    def grep_freq(modelname):
        grepped = ""
        if "@" in modelname:
            grepped = modelname.split("@")[-1].strip()
        return grepped

    # _____ execute_create ______
    def execute_create(tablename, cols_and_types):
        con.execute(_create_table_statement(tablename, cols_and_types))

    # ------------------ BEGIN create_database
    sqlite3.register_adapter(Decimal, adapt_decimal)
    sqlite3.register_converter("DECIMAL", convert_decimal)

    decimal.getcontext().prec = 24

    """return a new in-memory connection"""
    con = sqlite3.connect(
        ":memory:", detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None, uri=True
    )
    attach_spyu(con)
    con.create_function("grep_freq", 1, grep_freq)

    con.execute(
        "create table offers ( offerRowID INTEGER PRIMARY KEY"
        " AUTOINCREMENT NOT NULL, hash TEXT, address TEXT, ts timestamp"
        ", extra TEXT DEFAULT '')"
    )

    execute_create("activity.caps.transfer", ["protocol TEXT"])
    execute_create("com.payment.debit-notes", ["accept_timeout INTEGER"])
    execute_create("com.payment.platform", ["kind TEXT", "address TEXT"])
    execute_create("com.pricing", ["model TEXT"])
    execute_create(
        "com.pricing.model.linear.coeffs",
        ["duration_sec DECIMAL", "cpu_sec DECIMAL", "fixed FLOAT"],
    )
    execute_create("com.scheme", ["name TEXT", "interval_sec INTEGER"])
    execute_create(
        "inf.cpu",
        [
            "architecture TEXT",
            'capabilities TEXT DEFAULT "[]"',
            "cores INTEGER",
            'model TEXT DEFAULT ""',
            "threads INTEGER",
            'vendor TEXT DEFAULT ""',
        ],
    )
    execute_create("inf.mem", ["gib FLOAT"])
    execute_create("inf.storage", ["gib FLOAT"])
    execute_create("node.debug", ["subnet TEXT"])
    execute_create("node.id", ["name TEXT"])
    execute_create(
        "runtime", ["name TEXT", "version TEXT", 'capabilities DEFAULT "[]"']
    )
    execute_create("srv.caps", ["multi_activity TEXT"])
    con.execute(
        "create table extra ( offerRowID INTEGER NOT NULL"
        " REFERENCES offers(offerRowID), json TEXT DEFAULT '{}'"
        ", extra TEXT DEFAULT '')"
    )
    return con


# ++++++++++++ build_database +++++++++++++
def build_database(con, offers):
    """add each offer's details to the database
    { 'timestamp': FLOAT/STR, 'offer-id': <hash:str>,
            'issuer-address': <0xhash:str>,
            'props': { ... }
    }
    required by OfferLookup
    """

    cur = con.cursor()

    # offers table
    for offer in offers:
        # offers
        cur.execute(
            "INSERT INTO offers ('hash', 'address', 'ts') VALUES " "(?, ?, ?)",
            (offer["offer-id"], offer["issuer-address"], offer["timestamp"]),
        )

        lastrow = cur.lastrowid

        def _insert_record(*args):
            insert_record(con, offer, lastrow, *args)

        props = offer["props"]
        # activity.caps.transfer
        _insert_record(
            "activity.caps.transfer",
            "protocol",
            str(props["golem.activity.caps.transfer.protocol"]),
        )

        # com.payment.debit-notes
        _insert_record(
            "com.payment.debit-notes",
            "accept_timeout",
            offer["props"]["golem.com.payment.debit-notes.accept-timeout?"],
        )

        # com.payment.platform
        platform_info = find_platform_keys(offer["props"])
        for t in platform_info:
            # debug.dlog(t)
            _insert_record("com.payment.platform", "kind", t[0], "address", t[1])
            break  # for now assume all are equivalent

        # com.pricing
        _insert_record(
            "com.pricing", "model", offer["props"]["golem.com.pricing.model"]
        )
        if offer["props"]["golem.com.pricing.model"] == "linear":
            # get linears coeffs given usage vector
            dict_of_linear_coeffs = dictionary_of_linear_coeffs(
                offer["props"]["golem.com.usage.vector"],
                offer["props"]["golem.com.pricing.model.linear.coeffs"],
            )
            _insert_record(
                "com.pricing.model.linear.coeffs",
                "duration_sec",
                Decimal(dict_of_linear_coeffs["duration_sec"]),
                "cpu_sec",
                Decimal(dict_of_linear_coeffs["cpu_sec"]),
                "fixed",
                Decimal(dict_of_linear_coeffs["fixed"]),
            )

        # com.scheme.payu
        scheme_name, scheme_field_name = find_scheme(offer["props"])
        _insert_record(
            "com.scheme",
            "name",
            scheme_name,
            "interval_sec",
            offer["props"].get(scheme_field_name, ""),
        )

        # inf.cpu
        _insert_record(
            "inf.cpu",
            "architecture",
            props["golem.inf.cpu.architecture"],
            "cores",
            props["golem.inf.cpu.cores"],
            "threads",
            props["golem.inf.cpu.threads"],
        )

        if props["golem.runtime.name"] == "vm":
            try:
                con.execute(
                    "UPDATE 'inf.cpu' SET ( 'capabilities', 'model',"
                    "'vendor' ) = ( ?, ?, ? ) WHERE offerRowID = ?",
                    (
                        json.dumps(props["golem.inf.cpu.capabilities"]),
                        props["golem.inf.cpu.model"],
                        props["golem.inf.cpu.vendor"],
                        lastrow,
                    ),
                )
            except KeyError:
                # some vm's don't provide capabilities
                pass

        # node.debug
        _insert_record("node.debug", "subnet", props["golem.node.debug.subnet"])

        # node.id
        _insert_record("node.id", "name", props["golem.node.id.name"])

        # runtime
        _insert_record(
            "runtime",
            "name",
            props["golem.runtime.name"],
            "version",
            props["golem.runtime.version"],
        )

        if props["golem.runtime.name"] == "vm":
            try:
                con.execute(
                    "UPDATE 'runtime' SET ( 'capabilities' ) = ( ? )"
                    " WHERE offerRowID = ?",
                    (str(props["golem.runtime.capabilities"]), lastrow),
                )
            except KeyError:
                # some vm's do not have a vpn
                pass

        # srv.caps
        _insert_record(
            "srv.caps", "multi_activity", str(props["golem.srv.caps.multi-activity"])
        )

        # extra

        class DatetimeEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, datetime.datetime):
                    return str(o)
                return super(datetime, self).default(o)

            # or return super().default(o)

        _insert_record("extra", "json", json.dumps(offer, cls=DatetimeEncoder))
