
activate_this = "/home/kimura/usr/lib/pyvenvs/podiomynd/bin/activate_this.py"
try:
    execfile(activate_this, { '__file__': activate_this })
except IOError:
    pass

import api

api.sync_threads()

