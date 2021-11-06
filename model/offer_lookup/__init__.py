from model.sql import create_database
from .lookup import list_offers
import sys # debug
# from . lookupoffers import lookupoffers
class OfferLookup():
    async def __call__(self, id_, sql):
        """d/l offers, recreate database, execute sql
        , marshal results into json, return json or none on error"""
        offers = await list_offers("devnet-beta")

        con = create_database()

        print(f"database created...{con}")
        sys.exit(1)
        
