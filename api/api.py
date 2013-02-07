# vim: set fdm=marker :


# {{{ Imports

import os.path
import json
import pypodio2.api as podio_api

# }}}


def f():
    with open(os.path.expanduser("~/.podio")) as f:
        password = f.next().strip()
    client = podio_api.OAuthClient("api-test", "pnr83r17SiK2LOo0sq4yStcVMx6CLsHTGX4ToOPnsO15lvrp48VpUQPokHs7ohkf",
                                   "kimura@mynd.jp", password)
    apps = client.Application.list_in_space(client.Space.find_by_url("https://myndjp.podio.com/development/"))
    deriverables_app_id = [ x for x in apps if x["config"]["name"] == "Deliverables" ][0]["app_id"]
    print json.dumps(client.Item.filter(deriverables_app_id, { "limit": 200 }), ensure_ascii= False, indent= 2).encode("utf-8")
    # print len(client.Stream.find_all())
    # for item in client.Stream.find_all():
    #     print item["type"]
    # print json.dumps(client.Application.list_in_space(client.Space.find_by_url("https://myndjp.podio.com/development/")), ensure_ascii= False, indent= 2).encode("utf-8")
    # print json.dumps(len(client.Item.filter(1241680, {})["items"]), ensure_ascii= False, indent= 2).encode("utf-8")
    # print json.dumps(client.Item.transport.GET(url= "/comment/%s/%s/" % ( "item", "32851146" )), ensure_ascii= False, indent= 2).encode("utf-8")


if __name__ == "__main__":
    f()


