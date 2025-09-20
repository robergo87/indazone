from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from components.master import MasterWindow, load_css
from commands._base import CommandParser, register_client_command


argparser = CommandParser("focus")
argparser.add_argument("direction", type=str, choices=["left", "right", "up", "down"])

def execute(args, master, component=None):
    if args.direction == "left":
        master.trigger_focus_left()
    if args.direction == "right":
        master.trigger_focus_right()
    if args.direction == "up":
        master.trigger_focus_up()
    if args.direction == "down":
        master.trigger_focus_down()
    return "Done"

register_client_command("focus", argparser, execute)

