from collections import namedtuple


def select_rows(max_cpu_hr=None, max_dur_hr=None, start_fee_max=None):
    """build a sql select statement when either update or refreshing
    and return text"""
    feature_filter = ""

    # if feature filter
    if False:
        feature_filter = self.feature_entryframe.entryVar.get()
    feature_filter = ""

    # ss = f"""
    #     select 'node.id'.offerRowID
    #     , 'node.id'.name
    #     , 'offers'.address
    #     , 'com.pricing.model.linear.coeffs'.cpu_sec
    #     , 'com.pricing.model.linear.coeffs'.duration_sec
    #     , 'com.pricing.model.linear.coeffs'.fixed
    #     , 'inf.cpu'.cores
    #     , 'inf.cpu'.threads
    #     , 'runtime'.version
    #     , MAX('offers'.ts) AS most_recent_timestamp
    #     , (select 'runtime'.version FROM 'runtime'
    #         ORDER BY 'runtime'.version DESC LIMIT 1) AS highest_version
    #     , 'inf.cpu'.brand AS modelname
    #     , (SELECT grep_freq('inf.cpu'.brand)) AS freq
    #     , 'com.payment.platform'.kind AS token_kind
    #     , (
    #         SELECT json_group_array(value) FROM
    #         ( SELECT value FROM json_each('inf.cpu'.[capabilities]) )
    #      ) AS features
    #     , (
    #         SELECT json_group_array(value) FROM
    #         ( SELECT value FROM json_each('inf.cpu'.[capabilities])
    #         WHERE json_each.value LIKE '%{feature_filter}%'
    #         )
    #      ) AS featuresFiltered
    #     , ROUND('inf.mem'.gib,2) AS mem_gib
    #     , ROUND('inf.storage'.gib,2) AS storage_gib
    #     FROM 'node.id'
    #     JOIN 'offers' USING (offerRowID)
    #     JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)
    #     JOIN 'runtime'  USING (offerRowID)
    #     JOIN 'inf.cpu' USING (offerRowID)
    #     JOIN 'com.payment.platform' USING (offerRowID)
    #     JOIN 'inf.mem' USING (offerRowID)
    #     JOIN 'inf.storage' USING (offerRowID)
    #     WHERE 'runtime'.name = 'vm'
    # """

    ss = f"""
        select 'node.id'.offerRowID
        , 'node.id'.name
        , 'offers'.address
        , 'com.pricing.model.linear.coeffs'.cpu_sec
        , 'com.pricing.model.linear.coeffs'.duration_sec
        , 'com.pricing.model.linear.coeffs'.fixed
        , 'inf.cpu'.cores
        , 'inf.cpu'.threads
        , 'runtime'.version
        , 'extra'.json
        , MAX('offers'.ts) AS most_recent_timestamp
        , 'inf.cpu'.brand AS modelname
        , (SELECT grep_freq('inf.cpu'.brand)) AS freq
        , 'com.payment.platform'.kind AS token_kind
        , (
            SELECT json_group_array(value) FROM
            ( SELECT value FROM json_each('inf.cpu'.capabilities) )
         ) AS features
        , (
            SELECT json_group_array(value) FROM
            ( SELECT value FROM json_each('inf.cpu'.[capabilities])
            WHERE json_each.value LIKE '%{feature_filter}%'
            )
         ) AS featuresFiltered
        , ROUND('inf.mem'.gib,2) AS mem_gib
        , ROUND('inf.storage'.gib,2) AS storage_gib
        FROM 'node.id'
        JOIN 'offers' USING (offerRowID)
        JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)
        JOIN 'runtime'  USING (offerRowID)
        JOIN 'inf.cpu' USING (offerRowID)
        JOIN 'com.payment.platform' USING (offerRowID)
        JOIN 'inf.mem' USING (offerRowID)
        JOIN 'inf.storage' USING (offerRowID)
        JOIN 'extra' USING (offerRowID)
        WHERE 'runtime'.name = 'vm'
        GROUP BY 'offers'.address
    """

    # check for lastversion
    if False:
        ss += " AND 'runtime'.version = highest_version"

    epsilon = "0.000000001"

    def from_secs(decstr):
        epsilonized = Decimal(decstr) / Decimal("3600.0")
        return epsilonized

    # check cpusec filters
    if max_cpu_hr != None:
        max_cpu_sec = from_secs(float(max_cpu_hr))
        ss += (
            f" AND 'com.pricing.model.linear.coeffs'.cpu_sec - {max_cpu_sec}"
            f" <=  {epsilon}"
        )

    # check duration sec filters
    if max_dur_hr != None:
        max_dur_sec = from_secs(float(max_dur_hr))
        ss += (
            f" AND 'com.pricing.model.linear.coeffs'.duration_sec "
            f" - {max_dur_sec} < {epsilon}"
        )

    # check start filter
    if start_fee_max != None:
        start_fee_max = float(start_fee_max)
        ss += f" AND 'com.pricing.model.linear.coeffs'.fixed <= {start_fee_max}"

    # f/u check feature
    # if (
    #     self.feature_entryframe.whether_checked
    #     and self.feature_entryframe.entryVar.get()
    # ):
    #     ss += ""
    #     ss += f"""
    #          AND json_array_length(filteredFeatures) > 0
    #         """

    # implement ordering logic
    # if self.order_by_last:
    #     ss += " GROUP BY 'offers'.address"
    #     ss += f" ORDER BY {self.order_by_last}"
    #     ss += " COLLATE NOCASE"
    #     pass
    # else:
    #     path_tuple = self.treeframe._model_sequence_from_headings()
    #     ss += " GROUP BY 'offers'.address"
    #     ss += " ORDER BY "
    #     for i in range(len(path_tuple) - 1):
    #         ss += f"{path_tuple[i]}, "
    #     ss += f"{path_tuple[len(path_tuple)-1]}"
    #     ss += " COLLATE NOCASE"
    print(ss)
    return ss
