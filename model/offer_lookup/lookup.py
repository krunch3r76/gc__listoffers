# lookup.py
# interact with stats/yagna api to download the text of the current offers
import sys  # debug

import asyncio
from asyncio import TimeoutError
from datetime import datetime, timezone
import json
import sys
import pathlib
import debug

import importlib

yapapi_loader = importlib.util.find_spec("yapapi")

if yapapi_loader:
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


async def _list_offers(subnet_tag: str):
    """interact with the yagna daemon to query for offers and return a
    list of dictionary objects describing them
    pre: none
    in: subnet to filter results against
    out: list of offer dictionary objects
    post: none
    """

    @dataclass
    class MyPayload(yapapi.payload.Payload):
        """custom payload for demand builder that filters for vm runtimes only"""

        """
        required by: _list_offers
        """
        runtime: str = yapapi.props.base.constraint(
            yapapi.props.inf.INF_RUNTIME_NAME, default=yapapi.props.inf.RUNTIME_VM
        )

    # fp = open("debugmsg.txt", "w")
    conf = Configuration()  # this configures access to the yagna daemon
    # using the environment appkey
    async with conf.market() as client:
        market_api = Market(client)
        dbuild = DemandBuilder()
        dbuild.add(yp.NodeInfo(name="some scanning node", subnet_tag=subnet_tag))
        dbuild.add(yp.Activity(expiration=datetime.now(timezone.utc)))
        await dbuild.decorate(MyPayload())
        debug.dlog(dbuild)
        offers = []
        offer_ids_seen = set()
        dupcount = 0
        try:
            async with market_api.subscribe(
                dbuild.properties, dbuild.constraints
            ) as subscription:
                offer_d = dict()
                ai = subscription.events().__aiter__()
                timed_out = False
                while not timed_out:
                    offer_d.clear()
                    try:
                        event = await asyncio.wait_for(
                            ai.__anext__(), timeout=18
                        )  # <class 'yapapi.rest.market.OfferProposal'>
                        offer_d["offer-id"] = event.id
                        if offer_d["offer-id"] not in offer_ids_seen:
                            offer_ids_seen.add(offer_d["offer-id"])
                            offer_d["timestamp"] = datetime.now()  # note, naive
                            offer_d["issuer-address"] = event.issuer
                            offer_d["props"] = event.props  # dict
                            offers.append(dict(offer_d))
                            print(
                                f"unfiltered offers collected so far on all {subnet_tag}:"
                                f" {len(offers)}",
                                end="\r",
                            )
                            # a dict copy, i.e. with a unique handle
                        else:
                            dupcount += 1
                            debug.dlog(f"duplicate count: {dupcount}")
                    except TimeoutError as e:
                        timed_out = True
                    except Exception as e:
                        print(f"unhandled exception in lookup.py, marked timeout: {e}")
                        timed_out = True
            print("")
            debug.dlog(f"number of offer_ids_seen: {len(offer_ids_seen)}")
            return offers

        except ya_market.exceptions.ApiException as e:
            raise e


def _list_offers_on_stats(send_end, subnet_tag: str):
    """send a GET request to the stats api to extract a listing of offers
     then return them
    pre: outbound https connections permitted
    in: multiprocessing pipe send end, subnet tag to filter results against
    out: list of offer dictionary objects or list of length one with 'error'
     sent over pipe
    post: none
    """
    offers = []
    result_list = []
    try:
        debug.dlog("trying stats")
        try:
            with urllib.request.urlopen(
                "https://api.stats.golem.network/v1/network/online"
            ) as response:
                debug.dlog(
                    f"stats http response status: {response.status}"
                    + f" with reason phrase: {response.msg}",
                    1,
                )
                result_list = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            if "CERTIFICATE_VERIFY_FAILED" in e.__str__():
                import ssl

                ssl._create_default_https_context = ssl._create_unverified_context
                with urllib.request.urlopen(
                    "https://api.stats.golem.network/v1/network/online",
                ) as response:
                    debug.dlog(
                        f"stats http response status: {response.status}"
                        + f" with reason phrase: {response.msg}",
                        1,
                    )
                    result_list = json.loads(response.read().decode("utf-8"))
            else:
                offers = ["error"]
    except Exception as e:
        offers = ["error"]
    else:
        offer_d = dict()
        import pprint

        for result in result_list:
            props = result["data"]
            # consider processing result['online'] which
            # so far is invariably true
            if (
                props["golem.runtime.name"] == "vm"
                and props["golem.node.debug.subnet"] == subnet_tag
            ):
                offer_d["timestamp"] = datetime.fromisoformat(result["updated_at"])
                offer_d["offer-id"] = 0
                offer_d["issuer-address"] = result["node_id"]
                offer_d["props"] = props
                offer_d["earnings_total"] = result["earnings_total"]
                offer_d["last_benchmark"] = result["last_benchmark"]
                offers.append(offer_d.copy())
                offer_d.clear()

    send_end.send(offers)


async def list_offers(subnet_tag: str, manual_probing=False):
    """query stats api otherwise scan yagna for offers then
    debug.dlog("listoffers called")
    return offers as a list of dictionary objects"""

    """
    called by: OfferLookup()
    pre: none
    in: subnet to filter results against
    out: list of offer dictionary objects, which may be empty
    post: none
    calls: _list_offers || _list_offers_on_stats
    raises: MissingConfiguration || ApiException || ClientConnectorError
    """
    offers = None
    fallback = False

    if not manual_probing:
        # launch non-asynchronous routine for https to stats
        recv_end, send_end = multiprocessing.Pipe(False)
        p = multiprocessing.Process(
            target=_list_offers_on_stats, args=(send_end, subnet_tag), daemon=True
        )
        p.start()

        # asynchronously await a response from over pipe
        while not recv_end.poll():
            await asyncio.sleep(0.01)
        offers = recv_end.recv()
        # else:
        #     offers=['error']

        if len(offers) > 0 and offers[0] == "error":  # review TODO
            fallback = True

    if (fallback or manual_probing) and yapapi_loader:
        offers = []
        if fallback:
            print(
                "there was a problem connecting to stats, falling back to probing."
                " this might take awhile"
            )
            debug.dlog("falling back to offer probe")
        try:
            offers = await _list_offers(subnet_tag)
        except yapapi.rest.configuration.MissingConfiguration as e:
            debug.dlog("raising " "yapapi.rest.configuration.MissingConfiguration")
            raise e
        except ya_market.exceptions.ApiException as e:
            raise e
        except aiohttp.client_exceptions.ClientConnectorError as e:
            raise e
        except Exception as e:
            debug.dlog(e)
            debug.dlog(type(e))
            debug.dlog(e.__class__.__name__)
    elif fallback:
        print(
            "there was a problem connecting to stats and fallback was not"
            " available! make sure you are connected"
            " to the internet. if so, stats may be unavailable."
            " you can try running yagna to perform a manual probe."
        )
        offers = []
    return offers
