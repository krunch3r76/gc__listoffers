# sql.py
import sqlite3
import sys # debug
import datetime
import itertools
import decimal
from decimal import Decimal
import json

def _create_table_statement_1(tablename, cols_and_types):
    def substatement():
        # created a comma delimited list of each tuple (colname, native_type)
        s=""
        for col_and_type_tuple in cols_and_types:
            s+=f"{col_and_type_tuple[0]} {col_and_type_tuple[1]}, "
        s=s[:-2]
        return s

    statement=f"create table '{tablename}' ( ROWID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, offerRowID INTEGER, {substatement()}, extra TEXT DEFAULT '')"
    return statement

    
def _create_table_statement(tablename, cols_and_types):
    def substatement():
        # created a comma delimited list of each column description
        s=""
        for col_and_type_s in cols_and_types:
            s+=f"{col_and_type_s}, "
        s=s[:-2]
        return s

    statement=f"create table '{tablename}' ( ROWID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, offerRowID INTEGER NOT NULL, {substatement()}, extra TEXT DEFAULT '' )"

    return statement





def create_database():
    def adapt_decimal(d):
        return str(d)

    def convert_decimal(s):
        return Decimal(s.decode('utf-8'))

    sqlite3.register_adapter(Decimal, adapt_decimal)
    sqlite3.register_converter("DECIMAL", convert_decimal)

    decimal.getcontext().prec=24

    """return a new in-memory connection"""
    con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES, isolation_level=None)

    con.execute("create table offers ( offerRowID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, hash TEXT, address TEXT, ts timestamp, extra TEXT DEFAULT '')")

    def execute_create(tablename, cols_and_types):
        con.execute( _create_table_statement(tablename, cols_and_types) )

    execute_create('activity.caps.transfer',      [ 'protocol TEXT' ] )
    execute_create('com.payment.debit-notes',   [ 'accept_timeout INTEGER' ] )
    execute_create('com.payment.platform',      [ 'kind TEXT', 'address TEXT' ] )
    execute_create('com.pricing',               [ 'model TEXT' ] )
    execute_create('com.pricing.model.linear.coeffs',   [ "duration_sec DECIMAL", "cpu_sec DECIMAL", "fixed FLOAT" ])
    execute_create('com.scheme',                [ 'name TEXT', 'interval_sec INTEGER' ] )
    execute_create('inf.cpu',                   [ 'architecture TEXT', 'capabilities TEXT DEFAULT "[]"', 'cores INTEGER', 'model TEXT DEFAULT ""', 'threads INTEGER', 'vendor TEXT DEFAULT ""' ] )
    execute_create('inf.mem',                   [ 'gib FLOAT' ] )
    execute_create('inf.storage',               [ 'gib FLOAT' ] )
    execute_create('node.debug',                [ 'subnet TEXT' ] )
    execute_create('node.id',                   [ 'name TEXT'] )
    execute_create('runtime',                   [ 'name TEXT', 'version TEXT', 'capabilities DEFAULT "[]"'] )
    execute_create('srv.caps',                  [ 'multi_activity TEXT' ] )
    con.execute("create table extra ( ROWID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, offerRowID INTEGER NOT NULL, json TEXT DEFAULT '{}', extra TEXT DEFAULT '')")
    return con





"""notes
the offer element props looks like:
{
     "golem.activity.caps.transfer.protocol": [
          "https", "http", "gftp"
     ],
     "golem.com.payment.debit-notes.accept-timeout?": 240,
     "golem.com.payment.platform.erc20-rinkeby-tglm.address": "0xe4012f5065d334f7f622051140048c9dc379ad30",
     "golem.com.payment.platform.zksync-rinkeby-tglm.address": "0xe4012f5065d334f7f622051140048c9dc379ad30",
     "golem.com.pricing.model": "linear",
     "golem.com.pricing.model.linear.coeffs": [
          5e-05,
          0.0001,
          0.0
     ],
     "golem.com.scheme": "payu",
     "golem.com.scheme.payu.interval_sec": 120.0,
     "golem.com.usage.vector": [
          "golem.usage.duration_sec", "golem.usage.cpu_sec"
     ],
     "golem.inf.cpu.architecture": "x86_64",
     "golem.inf.cpu.cores": 4,
     "golem.inf.cpu.threads": 1,
     "golem.inf.mem.gib": 4.0,
     "golem.inf.storage.gib": 20.0,
     "golem.node.debug.subnet": "devnet-beta",
     "golem.node.id.name": "mbenke",
     "golem.runtime.name": "wasmtime",
     "golem.runtime.version": "0.2.1",
     "golem.srv.caps.multi-activity": true,
--------------------------------------------------------------
 [ golem.runtime.name == 'vm' ]
 ----------------------------------------------------------------
     "golem.inf.cpu.capabilities": [
        "sse3", "pclmulqdq", "dtes64", "monitor", "dscpl", "vmx", "smx", "eist", "tm2", "ssse3", "fma", "cmpxchg16b", "pdcm", "pcid", "sse41", "sse42", "x2apic", "movbe", "popcnt", "tsc_deadline", "aesni", "xsave", "osxsave", "avx", "f16c", "rdrand", "fpu", "vme", "de", "pse", "tsc", "msr", "pae", "mce", "cx8", "apic", "sep", "mtrr", "pge", "mca", "cmov", "pat", "pse36", "clfsh", "ds", "acpi", "mmx", "fxsr", "sse", "sse2", "ss", "htt", "tm", "pbe", "fsgsbase", "adjust_msr", "smep", "rep_movsb_stosb", "invpcid", "deprecate_fpu_cs_ds", "mpx", "rdseed", "rdseed", "adx", "smap", "clflushopt", "processor_trace", "sgx" ],
  
    "golem.inf.cpu.model": "Stepping 3 Family 6 Model 94",
    "golem.inf.cpu.vendor": "GenuineIntel",
    "golem.runtime.capabilities": [
        "vpn"
    ],
}
"""


def build_database(con, offers):
    """add each offer's details to the database
    { 'timestamp': FLOAT/STR, 'offer-id': <hash:str>, 'issuer-address': <0xhash:str>,
        'props': { ... }
    }
    required by OfferLookup
    """

    """
    def insert_record_1(offer, offerRowID, tablename, unique_cols, colvals):
        def to_csv():
            csv=""
            for unique_col in unique_cols:
                csv=csv + unique_col + ", "
            
            csv = csv[:-2]
            return csv

        def to_placeholders():
            placeholder_str="?, " # one for the offerRowID
            for _ in range(len(unique_cols)):
                placeholder_str+="?, "
            return placeholder_str[:-2]

        insert_statement=f"INSERT INTO '{tablename}' ('offerRowID', '{to_csv()}') VALUES ({to_placeholders()})"
        print()
        print(f"offerRowID: {offerRowID}")
        print(f"colvals: {colvals}")
        astuple=(offerRowID, *colvals)
        print(f"astuple: {astuple}")
        print(f"insert_statement: {insert_statement}, {astuple}")
        con.execute(insert_statement, astuple )
    """


    def insert_record(offer, offerRowID, tablename, *names_vals):
        # take every other input in names_vals to build the unique_cols list
        unique_cols=[]
        colvals=[]
        for i in range(0, len(names_vals), 2):
            unique_cols.append(names_vals[i])
            colvals.append(names_vals[i+1])

        def to_csv():
            csv=""
            for unique_col in unique_cols:
                csv=csv + "'" + unique_col + "'" + ", "
            
            csv = csv[:-2]
            return csv

        def to_placeholders():
            placeholder_str="?, " # one for the offerRowID
            for _ in range(len(unique_cols)):
                placeholder_str+="?, "
            return placeholder_str[:-2]

        insert_statement=f"INSERT INTO '{tablename}' ('offerRowID', {to_csv()}) VALUES ({to_placeholders()})"
        astuple=(offerRowID, *colvals)
        con.execute(insert_statement, astuple )



    cur = con.cursor()


    def find_platform_keys(props):
        """lists keynames pertaining to platforms tupling with the specific platform name
        so [ ('golem.com.payment.platform.erc20-rinkeby-tglm.address', 'erc20-rinkeby-tglm'), ('...')
        """
        ss='golem.com.payment.platform'
        platform_keys=[]
        for key, value in props.items():
            if key.startswith(ss):
                idx_to_kind = len(ss) + 1
                idx_to_kind_end = key.find('.', idx_to_kind)
                platform_keys.append( (key[idx_to_kind:idx_to_kind_end], value ) )
        return platform_keys


    def find_scheme(props):
        """looks up a the scheme value then builds the expected derived golem.com.scheme.<name>.interval_sec returning the name and key as a tuple"""
        scheme_name=props['golem.com.scheme']
        expected_field="golem.com.scheme." + scheme_name + ".interval_sec"
        return scheme_name, expected_field

    def dictionary_of_linear_coeffs(usage_vector,  coeffs):
        """populate a dictionary of { "duration_sec", "cpu_sec", "fixed" } and return"""
        d = dict()
        if usage_vector[0] == "golem.usage.duration_sec":
            d["duration_sec"] = coeffs[0]
            d["cpu_sec"] =coeffs[1]
        else:
            d["duration_sec"] = coeffs[1]
            d["cpu_sec"] = coeffs[0]
        d["fixed"]=coeffs[2]

        return d

    def debug_select(ss):
        print(ss)
        cur.execute(ss)
        for row in cur:
            print(row)

    def debug_print_table(tablename, rowid=None):
        ss=f"select * from '{tablename}'"
        if rowid:
            ss+=f" WHERE ROWID={rowid}"
        debug_select(ss)

    # offers table
    for offer in offers:
        # offers
        cur.execute("INSERT INTO offers ('hash', 'address', 'ts') VALUES (?, ?, ?)", (offer['offer-id'], offer['issuer-address'], offer['timestamp']) )
        lastrow=cur.lastrowid

        def _insert_record(*args):
            insert_record(offer, lastrow, *args)

        props = offer['props']

        # activity.caps.transfer
        _insert_record('activity.caps.transfer', 'protocol', str(props['golem.activity.caps.transfer.protocol']))

        # com.payment.debit-notes
        _insert_record('com.payment.debit-notes', 'accept_timeout', offer['props']['golem.com.payment.debit-notes.accept-timeout?'])

        # com.payment.platform
        platform_info = find_platform_keys(offer['props'])
        for t in platform_info:
            _insert_record('com.payment.platform', 'kind', t[0], 'address', t[1])

        # com.pricing
        _insert_record('com.pricing', 'model', offer['props']['golem.com.pricing.model'])
        if offer['props']['golem.com.pricing.model'] == "linear":
            # get linears coeffs given usage vector
            dict_of_linear_coeffs = dictionary_of_linear_coeffs(offer['props']['golem.com.usage.vector'], offer['props']['golem.com.pricing.model.linear.coeffs'])
            _insert_record('com.pricing.model.linear.coeffs', 'duration_sec', Decimal(dict_of_linear_coeffs['duration_sec']), 'cpu_sec', Decimal(dict_of_linear_coeffs['cpu_sec']), 'fixed', Decimal(dict_of_linear_coeffs['fixed']))

        # com.scheme.payu
        scheme_name, scheme_field_name = find_scheme(offer['props'])
        _insert_record('com.scheme', 'name', scheme_name, 'interval_sec', offer['props'][scheme_field_name])

        # inf.cpu
        _insert_record('inf.cpu', 'architecture', props['golem.inf.cpu.architecture'], 'cores', props['golem.inf.cpu.cores'], 'threads', props['golem.inf.cpu.threads'])
        if props['golem.runtime.name']=="vm":
            try:
                con.execute(
                        "UPDATE 'inf.cpu' SET ( 'capabilities', 'model', 'vendor' ) = ( ?, ?, ? ) WHERE offerRowID = ?"
                        , (str(props['golem.inf.cpu.capabilities']), props['golem.inf.cpu.model'], props['golem.inf.cpu.vendor'], lastrow)
                            )
            except KeyError:
                # some vm's don't provide capabilities
                pass

        # node.debug
        _insert_record('node.debug', 'subnet', props['golem.node.debug.subnet'])

        # node.id
        _insert_record('node.id', 'name', props['golem.node.id.name'])

        # runtime
        _insert_record('runtime', 'name', props['golem.runtime.name'], 'version', props['golem.runtime.version'])
        if props['golem.runtime.name']=="vm":
            try:
                con.execute(
                        "UPDATE 'runtime' SET ( 'capabilities' ) = ( ? ) WHERE offerRowID = ?"
                        , ( str(props['golem.runtime.capabilities']), lastrow )
                        )
            except KeyError:
                # some vm's do not have a vpn
                pass

        # srv.caps
        _insert_record('srv.caps', 'multi_activity', str(props['golem.srv.caps.multi-activity']))

        # extra

        class DatetimeEncoder(json.JSONEncoder):
           def default(self, o):
                if isinstance(o, datetime.datetime):
                    return str(o)
                return super(datetime, self).default(o) # or return super().default(o)



        _insert_record('extra', 'json', json.dumps(offer,cls=DatetimeEncoder))

    # debug_print_table('activity.caps.transfer')
