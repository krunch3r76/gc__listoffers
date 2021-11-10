from model.sql import create_database, build_database
from .lookup import list_offers
import sys # debug
import json
# from . lookupoffers import lookupoffers
class OfferLookup():

    def __init__(self):
        self._session_id="1"
        self._con = None

    async def __call__(self, id_, subnet_tag, sql):
        """d/l offers, recreate database, execute sql, return sqlite rows"""
        # print(f"[OfferLookup::__call__()] called with id {id_}")


        if id_ != self._session_id:
            # print(f"[OfferLookup::__call__()] replacing session calling list_offers with subnet_tag {subnet_tag}")
            offers = await list_offers(subnet_tag) # this is the one on mainnet

            if self._con:
                self._con.close()
            self._con = create_database()

            # print(f"[OfferLookup::__call__()] building database")
            build_database(self._con, offers)
            self._session_id=id_
            
        rows = self._con.execute(sql).fetchall()
        # print(f"[OfferLookup::__call__()] returning rows")
        return rows
