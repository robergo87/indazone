import argparse

from gi.repository import Gtk
from gi.repository import Pango, PangoCairo

from commands._base import CommandParser, register_client_command

def get_fonts():
    fontmap = PangoCairo.font_map_get_default()
    return [
        fam.get_name() for fam in fontmap.list_families()
    ]

argparser = CommandParser("filetree")
argparser.add_argument("command", type=str, choices=[
    "newfile", "newdir", "chmod", "copy", "rename", "delete",
    "font-inc", "font-dec", "fonts"
])

def execute(args, master, component=None):
    if args.command == "chmod":
        master.filetree.trigger_chmod()
    if args.command == "newfile":
        master.filetree.trigger_new_file()
    if args.command == "newdir":
        master.filetree.trigger_new_dir()
    if args.command == "copy":
        master.filetree.trigger_copy()
    if args.command == "rename":
        master.filetree.trigger_rename()
    if args.command == "delete":
        master.filetree.trigger_delete()
    if args.command == "font-inc":
        master.filetree.font_size +=1
        master.bufferlist.font_size +=1
        master.filetree.update_font()
        master.bufferlist.update_font()
        return True
    if args.command == "font-dec":
        master.filetree.font_size -=1
        master.bufferlist.font_size -=1
        master.filetree.update_font()
        master.bufferlist.update_font()
        return True
    if args.command == "fonts":
        return True, get_fonts()

register_client_command("filetree", argparser, execute)

argparser = CommandParser("set-filetree-font-family")
argparser.add_argument("family", type=str, choices=get_fonts())
def execute(args, master, component=None):
    master.filetree.font_family = args.family
    return master.filetree.update_font()
register_client_command("set-filetree-font-family", argparser, execute)


argparser = CommandParser("set-filetree-font-size")
argparser.add_argument("size", type=int)
def execute(args, master, component=None):
    master.filetree.font_size = args.size
    return master.filetree.update_font()
register_client_command("set-filetree-font-size", argparser, execute)
