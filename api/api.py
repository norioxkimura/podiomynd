# vim: set fdm=marker :


# {{{ Imports

import os.path
import json
from   time import sleep
from   codecs import open
import pypodio2.api as podio_api
from   datetime import datetime

# }}}


def log(msg):
    msg = "%s: %s" % ( datetime.today(), msg )
    print msg


def greedy(api, *pargs, **kargs):
    while True:
        try:
            result = api(*pargs, **kargs)
        except Exception, e:
            log("greedy(%s): Exception [%s]" % ( api, e ))
            sleep(60)
            continue
        break
    return result


def f():

    with open(os.path.expanduser("~/.podio")) as f:
        password = f.next().strip()
    client = podio_api.OAuthClient("api-test", "pnr83r17SiK2LOo0sq4yStcVMx6CLsHTGX4ToOPnsO15lvrp48VpUQPokHs7ohkf",
                                   "kimura@mynd.jp", password)
    apps = client.Application.list_in_space(client.Space.find_by_url("https://myndjp.podio.com/development/"))
    deriverables_app_id = [ x for x in apps if x["config"]["name"] == "Deliverables" ][0]["app_id"]

    limit, offset, items = 30, 0, []
    while True:
        result = greedy(client.Item.filter, deriverables_app_id, { "limit": limit, "offset": offset })
        print "Got %d items: %s" % ( len(result["items"]),
                                     reduce(lambda x, y: x + y,
                                            [ "{%s}" % item["title"] for item in result["items"] ]).encode("utf-8") )
        items += result["items"]
        offset += len(result["items"])
        if offset == result["total"]:
            break
    with open(os.path.join("transactions", "items.json"), "w", encoding= "utf-8") as f:
        items_dict = dict([ ( item["item_id"], item ) for item in items ])
        json.dump(items_dict, f, ensure_ascii= False, sort_keys= True, indent= 2)

    comments = {}
    for item in items:
        item_id = item["item_id"]
        comments[item_id] = greedy(client.Item.transport.GET, url= "/comment/item/%s/" % ( item_id ))
        print "Got %d comments of [%s]" % ( item["comment_count"], item["title"] )
    with open(os.path.join("transactions", "comments.json"), "w", encoding= "utf-8") as f:
        json.dump(comments, f, ensure_ascii= False, sort_keys= True, indent= 2)

    limit, offset, statuses = 30, 0, []
    while True:
        result = greedy(client.Stream.transport.GET, url= "/stream/?offset=%d&limit=%d" % ( offset, limit ))
        print "Got %d stream items: %s" % ( len(result), [ "{%s}" % item["type"] for item in result ] )
        statuses += result
        offset += len(result)
        if len(result) == 0:
            break
    with open(os.path.join("transactions", "statuses.json"), "w", encoding= "utf-8") as f:
        json.dump(statuses, f, ensure_ascii= False, sort_keys= True, indent= 2)


if __name__ == "__main__":
    f()


