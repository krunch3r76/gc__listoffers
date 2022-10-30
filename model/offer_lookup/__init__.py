from model.sql import create_database, build_database
from .lookup import list_offers
import sys  # debug
import json
import debug


import importlib

yapapi_loader = importlib.util.find_spec("yapapi")
if yapapi_loader:
    import aiohttp
    import yapapi
    import ya_market
# from . lookupoffers import lookupoffers

#
# this creates a dependency on yapapi and may be avoided using
# custom exceptions

#


class OfferLookup:

    # _-_-_-_- __init__ _-_-_-_-
    def __init__(self):
        self._session_id = "-1"
        self._con = None

    # _-_-_-_- __call __ _-_-_-_-
    async def __call__(self, id_, subnet_tag, sql, manual_probe=False, appkey=""):
        """find offers, recreate database, execute sql
        , return sqlite rows"""
        # print(f"[OfferLookup::__call__()] called with id {id_}")
        import os

        offers = []
        os.environ["YAGNA_APPKEY"] = (
            appkey if appkey != "" else os.environ.get("YAGNA_APPKEY", "")
        )
        rows = []

        if id_ != self._session_id:
            # scan offers anew
            try:
                async for offers_sub in list_offers(
                    event_timeout=5,
                    subnet_tag=subnet_tag,
                    manual_probing=manual_probe,
                ):
                    offers.extend(offers_sub)
            except ya_market.exceptions.ApiException as e:
                rows.extend(["error", e.status])  # 401 is invalid
                # application key
                debug.dlog(rows)
            except yapapi.rest.configuration.MissingConfiguration:
                rows.extend(["error", 401])
            except aiohttp.client_exceptions.ClientConnectorError:
                rows.extend(["error", 111])
            except Exception as e:
                print(f"unhandled exception {e}")
            else:
                if offers != None:  # kludge
                    from pprint import pformat

                    if len(offers) > 0:
                        debug.dlog(
                            f"outputting first two offers of type {type(offers[0])} returned by"
                            + f"list_offers routine: {pformat(offers[0])}"
                            + f"\n{pformat(offers[1])}",
                            2,
                        )

                    # recreate in memory database
                    if self._con:
                        self._con.close()
                    self._con = create_database()
                    build_database(self._con, offers)
                    self._session_id = id_

        if len(rows) == 0:
            cur = self._con.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            debug.dlog(sql)
            rows = cur.execute(sql).fetchall()
        # rows = self._con.execute(sql).fetchall()
        return rows
