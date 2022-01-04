from model.sql import create_database, build_database
from .lookup import list_offers
import sys # debug
import json
import debug
import aiohttp
# from . lookupoffers import lookupoffers

#
 # this creates a dependency on yapapi and may be avoided using custom exceptions
import yapapi
import ya_market
#

class OfferLookup():

    def __init__(self):
        self._session_id="1"
        self._con = None

    async def __call__(self, id_, subnet_tag, sql):
        """d/l offers, recreate database, execute sql, return sqlite rows"""

        # print(f"[OfferLookup::__call__()] called with id {id_}")
        rows = []
        if id_ != self._session_id:
            # scan offers anew
            try:
                offers = await list_offers(subnet_tag) # this is the one on mainnet
            except ya_market.exceptions.ApiException as e:
                rows.extend(['error', e.status]) # 401 is invalid application key
                debug.dlog(rows)
            except yapapi.rest.configuration.MissingConfiguration:
                rows.extend(['error', 401])
            except aiohttp.client_exceptions.ClientConnectorError:
                rows.extend(['error', 111])
            else:
                if offers != None: # kludge
                    if len(offers)>0:
                        debug.dlog(f"outputting first offer returned by list_offers routine: {offers[0]}",2)
                    if self._con:
                        self._con.close()

                    self._con = create_database()

                    build_database(self._con, offers)
                    self._session_id=id_
        if len(rows) == 0:
            cur = self._con.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            r = cur.fetchone()

            rows = cur.execute(sql).fetchall()

        # rows = self._con.execute(sql).fetchall()
        return rows
