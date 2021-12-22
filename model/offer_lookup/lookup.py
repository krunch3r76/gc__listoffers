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
from yapapi.props import inf
from yapapi.log import enable_default_logger
from yapapi.props.builder import DemandBuilder
from yapapi.rest import Configuration, Market, Activity, Payment  # noqa
import yapapi
import aiohttp
from dataclasses import dataclass

import multiprocessing
import urllib.request

examples_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(examples_dir))



@dataclass
class MyPayload(yapapi.payload.Payload):
    runtime: str = yapapi.props.base.constraint(yapapi.props.inf.INF_RUNTIME_NAME, default=yapapi.props.inf.RUNTIME_VM)


async def _list_offers(conf: Configuration, subnet_tag: str):

    # fp = open("debugmsg.txt", "w")

    async with conf.market() as client:
        market_api = Market(client)
        dbuild = DemandBuilder()
        dbuild.add(yp.NodeInfo(name="some scanning node", subnet_tag=subnet_tag))
        dbuild.add(yp.Activity(expiration=datetime.now(timezone.utc)))
        await dbuild.decorate(MyPayload())
        debug.dlog(dbuild)
        offers = []
        offer_ids_seen = set()
        dupcount=0
        try:
            async with market_api.subscribe(dbuild.properties, dbuild.constraints) as subscription:
                offer_d = dict()
                ai = subscription.events().__aiter__()
                timed_out=False
                while not timed_out:
                    offer_d.clear()
                    try:
                        event = await asyncio.wait_for(
                                ai.__anext__()
                                , timeout=12
                            ) # <class 'yapapi.rest.market.OfferProposal'>
                        offer_d["offer-id"]=event.id

                        if offer_d["offer-id"] not in offer_ids_seen:
                            offer_ids_seen.add(offer_d["offer-id"])
                            offer_d["timestamp"]=datetime.now() # note, naive
                            offer_d["issuer-address"]=event.issuer
                            offer_d["props"]=event.props # dict
                            offers.append(dict(offer_d)) # a dict copy, i.e. with a unique handle
                        else:
                            dupcount+=1
                            debug.dlog(f"duplicate count: {dupcount}")
                    except TimeoutError:
                        timed_out=True
            debug.dlog(f"number of offer_ids_seen: {len(offer_ids_seen)}")
            return offers

        except ya_market.exceptions.ApiException as e:
            raise e


def _list_offers_on_stats(send_end, subnet_tag: str):
    offers = []
    try:
        with urllib.request.urlopen('https://api.stats.golem.network/v1/network/online') as response:
            r = response.read().decode('utf-8')
            r = json.loads(r)
    except:
        debug.dlog("exception")
        offers = ['error']
    else:
        offer_d=dict()
        for result in r:
            props = result['data']
            if props['golem.runtime.name']=='vm' and props['golem.node.debug.subnet']==subnet_tag:
                offer_d["timestamp"]=datetime.now()
                offer_d["offer-id"]=0
                offer_d["issuer-address"]=result['node_id']
                offer_d["props"]=props
                offers.append(offer_d.copy())
                offer_d.clear()

    send_end.send(offers)


async def list_offers(subnet_tag: str):
    """scan yagna for offers then return results in a dictionary"""
    """called by OfferLookup"""
    offers = None
    fallback = False

    recv_end, send_end = multiprocessing.Pipe(False)
    p = multiprocessing.Process(target=_list_offers_on_stats, args=(send_end, subnet_tag), daemon=True)
    p.start()
    while not recv_end.poll():
        await asyncio.sleep(0.01)
    offers = recv_end.recv()

    if len(offers) > 0 and offers[0]=='error':
        fallback=True

    if fallback:
        debug.dlog("fallback to offer probe")
        try:
            offers = await _list_offers(
                        Configuration()
                        , subnet_tag
                        )
        except yapapi.rest.configuration.MissingConfiguration as e:
            debug.dlog("raising yapapi.rest.configuration.MissingConfiguration")
            raise e
        except ya_market.exceptions.ApiException as e:
            raise e
        except aiohttp.client_exceptions.ClientConnectorError as e:
            raise e
        except Exception as e:
            debug.dlog(e)
            debug.dlog(type(e))
            debug.dlog(e.__class__.__name__)

    return offers

