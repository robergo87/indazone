from os.path import dirname, abspath, join, exists

import threading
import queue
import traceback
import shlex

from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from components.master import MasterWindow, load_css
from commands._base import CommandParser, register_command, execute_command, register_client_command

from unixsocket import start_server


argparser = CommandParser("run")


def execute(argparser, master=None, component=None):
    win = MasterWindow(argparser.workdir, argparser.sessionid)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    load_css()

    def handle_request(message):
        result = queue.Queue()
        def inner(result):
            try:
                response = execute_command(message, client=True, master=win)
                result.put(response)
            except Exception as e:
                result.put([False, str(e) + "\n\n" + traceback.format_exc()])
        GLib.idle_add(inner, result)
        return result.get()
        
    def bg_server():
        start_server(argparser.sessionid, handle_request)

    worker_thread = threading.Thread(target=bg_server, daemon=True)
    worker_thread.start()

    def handle_cnf_file(cnf_path):
        if not exists(cnf_path):
            return
        with open(cnf_path) as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                args = shlex.split(line)
                try:
                    execute_command(args, client=True, master=win)
                except SystemExit:
                    print("Args causing error", args)
                    pass
    cnf_path = join(abspath(dirname(dirname(__file__))), "config.cnf")
    handle_cnf_file(cnf_path)
    cnf_path = abspath("~/.config/indazone.cnf")
    handle_cnf_file(cnf_path)
    Gtk.main()
    return "Done"

register_command("run", argparser, execute)


argparser = CommandParser("workdir")
def execute(args, master, component=None):
    return master.workdir
register_client_command("workdir", argparser, execute)


