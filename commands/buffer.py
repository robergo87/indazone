import argparse

from gi.repository import Gtk
from gi.repository import Pango, PangoCairo

from commands._base import CommandParser, register_client_command

def get_fonts():
    fontmap = PangoCairo.font_map_get_default()
    return [
        fam.get_name() for fam in fontmap.list_families()
    ]

argparser = CommandParser("buffer")
argparser.add_argument("command", type=str, choices=[
  "list", "prev", "next", "first", "last", "close", "save", "font-inc", "font-dec", "fonts"
])

def execute(args, master, component=None):
    if args.command == "font-inc":
        master.bufferlist.font_size +=1
        return master.bufferlist.update_font()
    if args.command == "font-dec":
        master.bufferlist.font_size -=1
        return master.bufferlist.update_font()
    if args.command == "fonts":
        return get_fonts()
    if args.command == "list":
        return master.editor.buffer_list
    if args.command == "prev":
        return master.editor.trigger_prev()
    if args.command == "next":
        return master.editor.trigger_next()
    if args.command == "first":
        return master.editor.trigger_first()
    if args.command == "last":
        return master.editor.trigger_last()
    if args.command == "close":
        if master.editor.current_buffer:
            return master.editor.trigger_close(master.editor.current_buffer)
        return False
    if args.command == "save":
        print("Saving")
        if master.editor.current_buffer:
            return master.editor.trigger_save(master.editor.current_buffer)
        return False
register_client_command("buffer", argparser, execute)

argparser = CommandParser("set-bufferlist-font-family")
argparser.add_argument("family", type=str, choices=get_fonts())
def execute(args, master, component=None):
    master.bufferlist.font_family = args.family
    return master.bufferlist.update_font()
register_client_command("set-bufferlist-font-family", argparser, execute)


argparser = CommandParser("set-bufferlist-font-size")
argparser.add_argument("size", type=int)
def execute(args, master, component=None):
    master.bufferlist.font_size = args.size
    return master.bufferlist.update_font()
register_client_command("set-bufferlist-font-size", argparser, execute)


argparser = CommandParser("open")
argparser.add_argument("filepath", type=str, default="")
def execute(args, master, component=None):
    return master.editor.trigger_open(args.filepath)
register_client_command("open", argparser, execute)

argparser = CommandParser("save")
argparser.add_argument("filepath", type=str, default="")
def execute(args, master, component=None):
    return master.editor.trigger_open(args.filepath)
register_client_command("save", argparser, execute)


argparser = CommandParser("close")
argparser.add_argument("filepath", type=str, default="")
def execute(args, master, component=None):
    return master.editor.trigger_close(args.filepath)
register_client_command("close", argparser, execute)

argparser = CommandParser("focus")
argparser.add_argument("filepath", type=str, default="")
def execute(args, master, component=None):
    return master.editor.trigger_focus(args.filepath)
register_client_command("focus", argparser, execute)

