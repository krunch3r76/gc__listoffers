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
import sqlite3

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
    from yapapi.config import ApiConfig

from dataclasses import dataclass

import multiprocessing
import urllib.request

examples_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(examples_dir))


async def _list_offers(subnet_tag: str, timeout=None, on_offer=None):
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
    conf = Configuration(
        api_config=ApiConfig()
    )  # this configures access to the yagna daemon
    # using the environment appkey
    async with conf.market() as client:
        market_api = Market(client)
        dbuild = DemandBuilder()
        dbuild.add(yp.NodeInfo(name="some scanning node", subnet_tag=subnet_tag))
        dbuild.add(yp.Activity(expiration=datetime.now(timezone.utc)))
        await dbuild.decorate(MyPayload())
        # offers.clear()
        # offers = []
        offer_ids_seen = set()
        dupcount = 0
        from pprint import pprint

        async with market_api.subscribe(
            dbuild.properties, dbuild.constraints
        ) as subscription:
            offer_d = dict()

            timeout_threshold_between_events = 2
            time_start = datetime.now()
            async for event in subscription.events():
                offer_d.clear()
                offer_d["offer-id"] = event.id
                if offer_d["offer-id"] not in offer_ids_seen:
                    offer_ids_seen.add(offer_d["offer-id"])
                    offer_d["timestamp"] = datetime.now()  # note, naive
                    offer_d["issuer-address"] = event.issuer
                    offer_d["props"] = event.props  # dict
                    on_offer(dict(offer_d))
                    # print(
                    #     f"unfiltered offers collected so far on all {subnet_tag}:"
                    #     f" {len(offers)}, \t\t\ttime: {(datetime.now() - time_start).seconds}",
                    #     end="\r",
                    # )
                    if (
                        datetime.now() - time_start
                    ).seconds > timeout_threshold_between_events:
                        break
                    # a dict copy, i.e. with a unique handle
                else:
                    dupcount += 1
                    debug.dlog(f"duplicate count: {dupcount}")
                # if (
                #     datetime.now() - time_start
                # ).seconds > timeout_threshold_between_events:
                #     return offers


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


async def list_offers(
    subnet_tag: str, manual_probing=False, timeout=1
):  # timeout not implemented yet
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

    class DatetimeEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return str(o)
            return super(datetime, self).default(o)

    def adapt_dictionary(python_dict):
        # convert to json string
        import json

        # return json.JSONEncoder().encode(python_dict)  # str
        return DatetimeEncoder().encode(python_dict)
        # return json.dumps(python_dict)  # str

    def convert_dictionary(json_object):
        # convert to python type
        # str -> dict
        import json

        rv = json.loads(json_object)
        # rv = json.JSONDecoder().decode(json_object_as_string)
        return rv

    def create_memory_connection():
        debug.dlog("CREATE")
        sqlite3.register_converter("DICT", convert_dictionary)
        sqlite3.register_adapter(dict, adapt_dictionary)

        con = sqlite3.connect(
            ":memory:", isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES
        )
        query = "CREATE TABLE offers_ (rowid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, issuer_address TEXT UNIQUE, full_record DICT)"
        con.execute(query)
        # query = "CREATE TABLE candidateOffers (rowid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, issuer_address TEXT UNIQUE, full_record DICT)"
        # con.execute(query)
        # query = "CREATE TABLE uniqueIssuers (rowid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, issuer_address TEXT UNIQUE)"
        # con.execute(query)

        return con

    # def add_candidateOffers(con, offers):
    #     # drop the current table rows and insert new offers
    #     query = "INSERT INTO offers (issuer_address, full_record) "

    def replace_offer(con, issuer, offer):
        query = "REPLACE INTO offers_ (issuer_address, full_record) VALUES (?, ?)"
        cur = con.cursor()
        cur.execute(query, (issuer, offer))

    def count_records(con):
        query = "SELECT COUNT(*) FROM offers_"
        cur = con.cursor()
        res = cur.execute(query)
        row = res.fetchone()
        return row[0]

    def records_to_list(con):
        offers = []
        query = "SELECT full_record FROM offers_"
        res = con.execute(query)
        for row in res:
            # debug.dlog(type(row[0]))
            offers.append(row[0])
        return offers

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
        else:
            yield offers

    if (fallback or manual_probing) and yapapi_loader:
        con = create_memory_connection()

        now = datetime.now()
        offers = []
        timed_out = False
        timeout_threshold = 10
        if fallback:
            print(
                "there was a problem connecting to stats, falling back to probing."
                " this might take awhile"
            )
            debug.dlog("falling back to offer probe")
        while not timed_out:
            try:
                offers = []
                # offers = await _list_offers(subnet_tag, timeout=2)
                await asyncio.wait_for(
                    _list_offers(subnet_tag, on_offer=lambda o: offers.append(o)),
                    timeout=180,
                )
                # 10212022 make a new in memory database or new table and perform a union operation
                # then compare count change, alternatively, compare and replace individually
                count_previous = count_records(con)
                for offer_dict in offers:
                    unity = replace_offer(
                        con, issuer=offer_dict["issuer-address"], offer=offer_dict
                    )
                count = count_records(con)
                changed = count - count_previous
                debug.dlog(f"count: {count}, changed: {changed}")
                if count > 0 and changed == 0 or (datetime.now() - now).seconds > 120:
                    timed_out = True
                    yield records_to_list(con)
                # set_length_before_union = len(offers_set)
                # from pprint import pprint

                # pprint(offers[0])
                # offers_set |= set(offers)
                # print(f"length of offers_set: {len(offers_set)}", flush=True)
                # if len(offers_set) != set_length_before_union:
                #     now = datetime.now()
                # else:
                #     timed_out = True
                # elapsed = (datetime.now() - now).seconds
                # if elapsed > timeout_threshold:
                #     timed_out = True
            # except yapapi.rest.configuration.MissingConfiguration as e:
            #     debug.dlog("raising " "yapapi.rest.configuration.MissingConfiguration")
            #     raise e
            except ya_market.exceptions.ApiException as e:
                raise e
            except aiohttp.client_exceptions.ClientConnectorError as e:
                raise e
            except asyncio.TimeoutError:
                for offer_dict in offers:
                    unity = replace_offer(
                        con, issuer=offer_dict["issuer-address"], offer=offer_dict
                    )
                timed_out = True
                yield records_to_list(con)
            except Exception as e:
                debug.dlog(e)
                debug.dlog(type(e))
                debug.dlog(e.__class__.__name__)
    # elif fallback:
    #     print(
    #         "there was a problem connecting to stats and fallback was not"
    #         " available! make sure you are connected"
    #         " to the internet. if so, stats may be unavailable."
    #         " you can try running yagna to perform a manual probe."
    #     )
    #     offers = []

    # here we can union sets of offers until so many offers come up empty (timeout)

    # return offers
