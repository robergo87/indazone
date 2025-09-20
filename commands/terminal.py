import argparse

from gi.repository import Gtk

from commands._base import CommandParser, register_client_command


argparser = CommandParser("terminal")
argparser.add_argument("command", type=str, choices=[
    "prev", "next", "first", "last", "open", "close", "split"
])

def execute(args, master, component=None):
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

