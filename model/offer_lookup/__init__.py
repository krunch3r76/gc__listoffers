from model.sql import create_database, build_database
from .lookup import list_offers
import sys # debug
import json
# from . lookupoffers import lookupoffers
class OfferLookup():


    async def __call__(self, id_, sql):
        """d/l offers, recreate database, execute sql
        , marshal results into json, return json or none on error"""
        offers = await list_offers("public-beta")
        con = create_database()
        build_database(con, offers)

        rows = con.execute(sql).fetchall()
        return rows
