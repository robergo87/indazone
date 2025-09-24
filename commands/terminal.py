import argparse

from gi.repository import Gtk
from gi.repository import Pango, PangoCairo

from commands._base import CommandParser, register_client_command

def get_fonts():
    fontmap = PangoCairo.font_map_get_default()
    return [
        fam.get_name() for fam in fontmap.list_families() if fam.is_monospace()
    ]

argparser = CommandParser("terminal")
argparser.add_argument("command", type=str, choices=[
    "prev", "next", "first", "last", "open", "close", "split", "font-inc", "font-dec"
])

def execute(args, master, component=None):
    if args.command == "font-inc":
        master.terminal_font_size += 1
        return master.trigger_update_terminal_font()
    if args.command == "font-dec":
        master.terminal_font_size -= 1
        return master.trigger_update_terminal_font()
    if not component:
        print("No component")
        return False
    if args.command == "split":
        return component.group.trigger_split()
    if args.command == "prev":
        return component.group.trigger_prev(True)
    if args.command == "next":
        return component.group.trigger_next(True)
    if args.command == "first":
        return component.group.trigger_first()
    if args.command == "last":
        return component.group.trigger_last()
    if args.command == "open":
        return component.group.trigger_open(True)
    if args.command == "close":
        return component.group.trigger_close()

register_client_command("terminal", argparser, execute)

argparser = CommandParser("set-terminal-font-family")
argparser.add_argument("family", type=str, choices=get_fonts())
def execute(args, master, component=None):
    master.terminal_font_family = args.family
    return master.trigger_update_terminal_font()
register_client_command("set-terminal-font-family", argparser, execute)


argparser = CommandParser("set-terminal-font-size")
argparser.add_argument("size", type=int)
def execute(args, master, component=None):
    master.terminal_font_size = args.size
    return master.trigger_update_terminal_font()
register_client_command("set-terminal-font-size", argparser, execute)


