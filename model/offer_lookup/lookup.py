# lookup.py
# interact with yagna api to download the text of the current offers
import sys # debug

import asyncio
from asyncio import TimeoutError
from datetime import datetime, timezone
import json
import sys
import pathlib
import debug

import ya_market
from yapapi import props as yp
from yapapi.log import enable_default_logger
from yapapi.props.builder import DemandBuilder
from yapapi.rest import Configuration, Market, Activity, Payment  # noqa
import yapapi

examples_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(examples_dir))



async def _list_offers(conf: Configuration, subnet_tag: str):
    async with conf.market() as client:
        market_api = Market(client)
        dbuild = DemandBuilder()
        dbuild.add(yp.NodeInfo(name="some scanning node", subnet_tag=subnet_tag))
        dbuild.add(yp.Activity(expiration=datetime.now(timezone.utc)))

        offers = []
        timeout_max_count=2
        try:
            async with market_api.subscribe(dbuild.properties, dbuild.constraints) as subscription:
                offer_d = dict()
                ai = subscription.events().__aiter__()
                timed_out=False
                while not timed_out:
                    try:
                        event = await asyncio.wait_for(
                                ai.__anext__()
                                , timeout=8
                            ) # <class 'yapapi.rest.market.OfferProposal'>
                        offer_d["timestamp"]=datetime.now() # note, naive
                        offer_d["offer-id"]=event.id
                        offer_d["issuer-address"]=event.issuer
                        offer_d["props"]=event.props # dict


                        offers.append(dict(offer_d)) # a dict copy, i.e. with a unique handle
                        offer_d.clear()
                    except TimeoutError:
                        timed_out=True
            return offers

        except ya_market.exceptions.ApiException as e:
            raise e

async def list_offers(subnet_tag: str):
    """scan yagna for offers then return results in a dictionary"""
    """called by OfferLookup"""
    offers = None
    try:
        offers = await _list_offers(
                    Configuration()
                    , subnet_tag
                    )
    except yapapi.rest.configuration.MissingConfiguration:
        raise ya_market.exceptions.ApiException
    except Exception as e:
        debug.dlog(e)
        debug.dlog(type(e))
        debug.dlog(e.__class__.__name__)
    return offers

