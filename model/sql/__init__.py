# sql.py
import sqlite3
import sys # debug


def _create_table_statement_1(tablename, cols_and_types):
    def substatement():
        # created a comma delimited list of each tuple (colname, native_type)
        s=""
        for col_and_type_tuple in cols_and_types:
            s+=f"{col_and_type_tuple[0]} {col_and_type_tuple[1]}, "
        s=s[:-2]
        return s

    statement=f"create table '{tablename}' ( ROWID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, offerRowID INTEGER, {substatement()}, extra TEXT )"
    print(statement)
    return statement

    
def _create_table_statement(tablename, cols_and_types):
    def substatement():
        # created a comma delimited list of each column description
        s=""
        for col_and_type_s in cols_and_types:
            s+=f"{col_and_type_s}, "
        s=s[:-2]
        return s

    statement=f"create table '{tablename}' ( ROWID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, offerRowID INTEGER, {substatement()}, extra TEXT )"

    print(statement)
    return statement





def create_database():
    """return a new in-memory connection"""
    con = sqlite3.connect(":memory:")

    con.execute("create table offers ( offerRowID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, hash TEXT, address TEXT)")

    def execute_create(tablename, cols_and_types):
        con.execute( _create_table_statement(tablename, cols_and_types) )

    execute_create('golem.activity.caps.transfer',      [ 'protocol TEXT' ] )
    execute_create('com.payment.debit-notes',   [ 'accept_timeout INTEGER' ] )
    execute_create('com.payment.platform',      [ 'kind TEXT', 'address TEXT' ] )
    execute_create('com.payment.pricing',       [ 'model TEXT', 'linear_coeffs TEXT' ] )
    execute_create('com.scheme.payu',           [ 'interval_sec INTEGER' ] )
    execute_create('com.usage',                 [ 'vector TEXT' ] )
    execute_create('inf.cpu',                   [ 'architecture TEXT', 'capabilities TEXT', 'cores INTEGER', 'model TEXT', 'threads INTEGER', 'vendor TEXT' ] )
    execute_create('inf.mem',                   [ 'gib FLOAT' ] )
    execute_create('inf.storage',               [ 'gib FLOAT' ] )
    execute_create('node.debug',                [ 'subnet TEXT' ] )
    execute_create('node.id',                   [ 'name TEXT'] )
    execute_create('runtime',                   [ 'name TEXT', 'version TEXT' ] )
    execute_create('srv.caps',                  [ 'multi_activity TEXT' ] )
    return con

