# _________ insert_record _________
def insert_record(con, offer, offerRowID, tablename, *names_vals):
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

    insert_statement=f"INSERT INTO '{tablename}' ('offerRowID',"\
        f" {to_csv()}) VALUES ({to_placeholders()})"
    astuple=(offerRowID, *colvals)
    con.execute(insert_statement, astuple )




# _________ find_platform_keys ____________
def find_platform_keys(props):
    """lists keynames pertaining to platforms tupling with the specific
    platform name so [ 
    ('golem.com.payment.platform.erc20-rinkeby-tglm.address'
    , 'erc20-rinkeby-tglm'), ('...')
    """
    ss='golem.com.payment.platform'
    platform_keys=[]
    for key, value in props.items():
        if key.startswith(ss):
            idx_to_kind = len(ss) + 1
            idx_to_kind_end = key.find('.', idx_to_kind)
            platform_keys.append( (key[idx_to_kind:idx_to_kind_end], value ) )
    return platform_keys


# ____________ find_scheme ____________
def find_scheme(props):
    """looks up a the scheme value then builds the expected
    derived golem.com.scheme.<name>.interval_sec returning the name and
    key as a tuple"""
    scheme_name=props['golem.com.scheme']
    expected_field="golem.com.scheme." + scheme_name + ".interval_sec"
    return scheme_name, expected_field



# ______________ dictionary_of_linear_coeffs _________
def dictionary_of_linear_coeffs(usage_vector,  coeffs):
    """populate a dictionary of { "duration_sec", "cpu_sec", "fixed" }
    and return"""
    d = dict()
    if usage_vector[0] == "golem.usage.duration_sec":
        d["duration_sec"] = coeffs[0]
        d["cpu_sec"] =coeffs[1]
    else:
        d["duration_sec"] = coeffs[1]
        d["cpu_sec"] = coeffs[0]
    d["fixed"]=coeffs[2]

    return d

# _____________ debug_select _____________
def debug_select(ss):
    print(ss)
    cur.execute(ss)
    for row in cur:
        print(row)

# ____________ debug_print_table ______________
def debug_print_table(tablename, rowid=None):
    ss=f"select * from '{tablename}'"
    if rowid:
        ss+=f" WHERE ROWID={rowid}"
    debug_select(ss)

