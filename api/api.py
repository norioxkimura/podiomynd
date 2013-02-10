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

    limit, offset, threads = 30, 0, []
    while True:
        result = greedy(client.Stream.transport.GET, url= "/stream/?offset=%d&limit=%d" % ( offset, limit ))
        print "Got %d stream items. %s" % ( len(result), [ "{%s}" % item["type"][0] for item in result ] )
        threads += result
        offset += len(result)
        if len(result) == 0:
            break
    with open(os.path.join("transactions", "threads.json"), "w", encoding= "utf-8") as f:
        json.dump(threads, f, ensure_ascii= False, sort_keys= True, indent= 2)

    items, statuses = {}, {}
    num_threads = len(threads)
    for i, thread in enumerate(threads):
        print "%d/%d:" % ( i + 1, num_threads ),
        if thread["type"] == "item":
            items[thread["id"]] = greedy(client.Item.find, thread["id"])
        elif thread["type"] == "status":
            statuses[thread["id"]] = greedy(client.Status.find, thread["id"])
        try:
            print "[%s]" % thread["type"], thread["app"]["config"]["name"]
        except:
            print "(%s)" % thread["space"]["name"]
    with open(os.path.join("transactions", "items.json"), "w", encoding= "utf-8") as f:
        json.dump(items, f, ensure_ascii= False, sort_keys= True, indent= 2)
    with open(os.path.join("transactions", "statuses.json"), "w", encoding= "utf-8") as f:
        json.dump(statuses, f, ensure_ascii= False, sort_keys= True, indent= 2)


if __name__ == "__main__":
    f()


