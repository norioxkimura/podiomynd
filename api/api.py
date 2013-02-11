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
    return markdown(t)


def download_all_threads():

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
            title = htmlof(item["title"])
            link = item["link"]
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
        thread_html["res"] = res
        s = template("thread", thread_html= thread_html)
        with open(os.path.join("html", "%s-%d.html" % ( thread["type"], thread["id"] )), "w", encoding= "utf-8") as f:
            f.write(s)


@route("/html/<filepath:path>")
def static(filepath):
    return static_file(filepath, root= os.path.join(os.path.dirname(__file__), "html"))


if __name__ == "__main__":
    bottle.run(host= "0.0.0.0", port= 18001, reloader= True)


