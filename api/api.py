# vim: set fdm=marker :


# {{{ Imports

from   os import mkdir
import os.path
import json
from   time import sleep
from   codecs import open
import bottle
from   bottle import template, static_file, route
import pypodio2.api as podio_api
from   datetime import datetime
from   markdown import markdown
from   itertools import takewhile

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


def u(t):
    return t.encode("utf-8")


def htmlof(t):
    return markdown(t.replace("\r\n\r\n", "\n\n").replace("\r\n", "  \n"), safe_mode= "escape")


def download_thread_details(client, threads):
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
    return (items, statuses)


def download_all_threads():

    with open(os.path.expanduser("~/.podio")) as f:
        password = f.next().strip()
    client = podio_api.OAuthClient("api-test", "pnr83r17SiK2LOo0sq4yStcVMx6CLsHTGX4ToOPnsO15lvrp48VpUQPokHs7ohkf",
                                   "kimura@mynd.jp", password)

    limit, offset, threads = 30, 0, []
    while True:
        result = greedy(client.Stream.transport.GET, url= "/stream/?offset=%d&limit=%d" % ( offset, limit ))
        print "Got %d stream items. %s" % ( len(result), [ "{%s}" % item["type"][0] for item in result ] )
        if len(result) == 0:
            break
        threads += result
        offset += len(result)
    with open(os.path.join("transactions", "threads.json"), "w", encoding= "utf-8") as f:
        json.dump(threads, f, ensure_ascii= False, sort_keys= True, indent= 2)

    items, statuses = download_thread_details(client, threads)
    with open(os.path.join("transactions", "items.json"), "w", encoding= "utf-8") as f:
        json.dump(items, f, ensure_ascii= False, sort_keys= True, indent= 2)
    with open(os.path.join("transactions", "statuses.json"), "w", encoding= "utf-8") as f:
        json.dump(statuses, f, ensure_ascii= False, sort_keys= True, indent= 2)


def sync_threads():

    with open(os.path.expanduser("~/.podio")) as f:
        password = f.next().strip()
    client = podio_api.OAuthClient("api-test", "pnr83r17SiK2LOo0sq4yStcVMx6CLsHTGX4ToOPnsO15lvrp48VpUQPokHs7ohkf",
                                   "kimura@mynd.jp", password)

    with open(os.path.join("transactions", "threads.json")) as f:
        threads = json.load(f)
    with open(os.path.join("transactions", "items.json")) as f:
        items = json.load(f)
    with open(os.path.join("transactions", "statuses.json")) as f:
        statuses = json.load(f)

    latest_update_on = max([ datetime.strptime(thread["last_update_on"], "%Y-%m-%d %H:%M:%S") for thread in threads ])
    limit, offset, threads_new = 30, 0, []
    while True:
        result = greedy(client.Stream.transport.GET, url= "/stream/?offset=%d&limit=%d" % ( offset, limit ))
        print "Got %d stream items. %s" % ( len(result), [ "{%s}" % item["type"][0] for item in result ] )
        if len(result) == 0:
            break
        result_new = takewhile(
            lambda x: datetime.strptime(x["last_update_on"], "%Y-%m-%d %H:%M:%S") > latest_update_on,
            result
        )
        result_new = list(result_new)
        threads_new += result_new
        if len(result_new) < len(result):
            break
        offset += len(result)
    # with open(os.path.join("transactions", "threads.json"), "w", encoding= "utf-8") as f:
    #     json.dump(dict(threads, **threads_new), f, ensure_ascii= False, sort_keys= True, indent= 2)

    items_new, statuses_new = download_thread_details(client, threads_new)
    # with open(os.path.join("transactions", "items.json"), "w", encoding= "utf-8") as f:
    #     json.dump(dict(items, **items_new), f, ensure_ascii= False, sort_keys= True, indent= 2)
    # with open(os.path.join("transactions", "statuses.json"), "w", encoding= "utf-8") as f:
    #     json.dump(dict(statuses, **statuses_new), f, ensure_ascii= False, sort_keys= True, indent= 2)


def generate_htmls():

    with open(os.path.join("transactions", "threads.json")) as f:
        threads = json.load(f)
    with open(os.path.join("transactions", "items.json")) as f:
        items = json.load(f)
    with open(os.path.join("transactions", "statuses.json")) as f:
        statuses = json.load(f)

    try:
        mkdir("html")
    except:
        pass
    for thread in threads:
        thread_html = {}
        if thread["type"] == "item":
            item = items[str(thread["id"])]
            title = item["title"]
            link = item["link"]
            descriptions = [ {
                                "name": field["label"],
                                "value": field["values"][0]["value"],
                             }
                             for field in item["fields"] if field["type"] == "text" ]
            res = [ {
                        "user": comment["user"]["name"],
                        "text": htmlof(comment["value"]),
                        "embed": {
                            "title": comment["embed"]["title"],
                            "description": comment["embed"]["description"] if comment["embed"]["description"] else ""
                        } if comment["embed"] else None
                    } for comment in item["comments"] ]
        elif thread["type"] == "status":
            status = statuses[str(thread["id"])]
            link = status["link"]
            descriptions = []
            title = status["value"]
            res = [ {
                        "user": comment["user"]["name"],
                        "text": htmlof(comment["value"]),
                        "embed": {
                            "title": comment["embed"]["title"],
                            "description": comment["embed"]["description"] if comment["embed"]["description"] else ""
                        } if comment["embed"] else None
                    }
                    for comment in status["comments"] ]
        else:
            continue
        thread_html["title"] = title
        thread_html["link"] = link
        thread_html["descriptions"] = descriptions
        thread_html["res"] = res
        s = template("thread", thread_html= thread_html)
        with open(os.path.join("html", "%s-%d.html" % ( thread["type"], thread["id"] )), "w", encoding= "utf-8") as f:
            f.write(s)


@route("/html/<filepath:path>")
def static(filepath):
    return static_file(filepath, root= os.path.join(os.path.dirname(__file__), "html"))


if __name__ == "__main__":
    bottle.run(host= "0.0.0.0", port= 18001, reloader= True)


