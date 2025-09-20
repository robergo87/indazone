from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from components.master import MasterWindow, load_css
from commands._base import CommandParser, register_client_command


argparser = CommandParser("exit")

def execute(args, master, component=None):
    GLib.idle_add(Gtk.main_quit)
    return "Done"

register_client_command("exit", argparser, execute)


argparser2 = CommandParser("echo")
argparser2.add_argument("message", type=str)

def execute(args, master, component=None):
    return args.message

register_client_command("echo", argparser2, execute)
