import argparse

from gi.repository import Gtk

from commands._base import CommandParser, register_client_command


argparser = CommandParser("filetree")
argparser.add_argument("command", type=str, choices=["newfile", "newdir", "chmod", "copy", "rename", "delete"])

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

register_client_command("filetree", argparser, execute)

