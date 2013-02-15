# vim: set fdm=marker :


# {{{ Imports

from   os import mkdir, utime
import os.path
import json
import time
from   time import sleep
from   codecs import open
import bottle
from   bottle import template, static_file, route
import pypodio2.api as podio_api
import calendar
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


def path(*pargs):
    return os.path.join(os.path.dirname(__file__), *pargs)


def download_threads(client, from_exclusive):
    limit, offset, threads = 30, 0, []
    while True:
        result = greedy(client.Stream.transport.GET, url= "/stream/?offset=%d&limit=%d" % ( offset, limit ))
        log("Got %d stream items. %s" % ( len(result), "".join([ "%s" % item["type"][0] for item in result ]) ))
        if len(result) == 0:
            break
        result_new = takewhile(
            lambda x: datetime.strptime(x["last_update_on"], "%Y-%m-%d %H:%M:%S") > from_exclusive,
            result
        )
        result_new = list(result_new)
        threads += result_new
        if len(result_new) < len(result):
            break
        offset += len(result)
    return threads


def download_thread_details(client, threads):
    items, statuses = {}, {}
    num_threads = len(threads)
    for i, thread in enumerate(threads):
        if thread["type"] == "item":
            items[str(thread["id"])] = greedy(client.Item.find, thread["id"])
        elif thread["type"] == "status":
            statuses[str(thread["id"])] = greedy(client.Status.find, thread["id"])
        log("%d/%d: [%s]" % ( i + 1, num_threads, thread["type"] ))
    return (items, statuses)


def load_json(path, default):
    try:
        with open(path) as f:
            result = json.load(f)
    except IOError, e:
        if e.errno != 2:
            raise
        result = default
    return result


def load_threads():
    threads = load_json(path("transactions", "threads.json"), [])
    items = load_json(path("transactions", "items.json"), {})
    statuses = load_json(path("transactions", "statuses.json"), {})
    return ( threads, items, statuses )


def dump_threads(threads, items, statuses):
    with open(path("transactions", "threads.json"), "w", encoding= "utf-8") as f:
        json.dump(threads, f, ensure_ascii= False, sort_keys= True, indent= 2)
    with open(path("transactions", "items.json"), "w", encoding= "utf-8") as f:
        json.dump(items, f, ensure_ascii= False, sort_keys= True, indent= 2)
    with open(path("transactions", "statuses.json"), "w", encoding= "utf-8") as f:
        json.dump(statuses, f, ensure_ascii= False, sort_keys= True, indent= 2)


def login():
    with open(os.path.expanduser("~/.podio")) as f:
        password = f.next().strip()
    client = podio_api.OAuthClient("api-test", "pnr83r17SiK2LOo0sq4yStcVMx6CLsHTGX4ToOPnsO15lvrp48VpUQPokHs7ohkf",
                                   "kimura@mynd.jp", password)
    return client


def parse_datetime(datetime_string):
    naive_utc = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
    naive_local = datetime.fromtimestamp(calendar.timegm(naive_utc.timetuple()))
    return naive_local


def get_latest_update_on(threads):
    if threads:
        return max([ parse_datetime(thread["last_update_on"]) for thread in threads ])
    else:
        return datetime(1900, 1, 1)  # ancient time


def sync_threads():
    client = login()
    threads, items, statuses = load_threads()
    latest_update_on = get_latest_update_on(threads)
    threads_new = download_threads(client, latest_update_on)
    if threads_new:
        items_new, statuses_new = download_thread_details(client, threads_new)
        dump_threads(threads + threads_new, dict(items, **items_new), dict(statuses, **statuses_new))
        generate_htmls(threads + threads_new, threads_new, items_new, statuses_new)


def generate_htmls(threads_all, threads_new, items_new, statuses_new):

    try:
        mkdir(path("html"))
    except:
        pass
    for thread in threads_new:
        thread_html = {}
        if thread["type"] == "item":
            item = items_new[str(thread["id"])]
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
            status = statuses_new[str(thread["id"])]
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
            log("generate_htmls(): type [%s]: skipped" % ( thread["type"] ))
            continue
        thread_html["title"] = title
        thread_html["link"] = link
        thread_html["descriptions"] = descriptions
        thread_html["res"] = res
        s = template("thread", template_lookup= [ path("views") ], thread_html= thread_html)
        fname = "%s-%d.html" % ( thread["type"], thread["id"] )
        with open(path("html", fname), "w", encoding= "utf-8") as f:
            f.write(s)
        last_update_naive_local = parse_datetime(thread["last_update_on"])
        last_update_timestamp = time.mktime(last_update_naive_local.timetuple())
        now_timestamp = time.mktime(datetime.now().timetuple())
        utime(path("html", fname), ( now_timestamp, last_update_timestamp ))
    index_html = ""
    for thread in threads_all:
        if thread["type"] != "item" and thread["type"] != "status":
            continue
        fname = "%s-%d.html" % ( thread["type"], thread["id"] )
        index_html += """<a target="_blank" href="%s">%s</a><br />\n""" % ( fname, fname )
    with open(path("html", "index.html"), "w", encoding= "utf-8") as f:
        f.write(index_html)


@route("/html/<filepath:path>")
def static(filepath):
    return static_file(filepath, root= path("html"))


if __name__ == "__main__":
    bottle.run(host= "0.0.0.0", port= 18001, reloader= True)


