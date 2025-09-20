import argparse

from gi.repository import Gtk

from commands._base import CommandParser, register_client_command


argparser = CommandParser("kb-set")
argparser.add_argument("scope", type=str, choices=["filetree", "bufferlist", "editor", "global", "terminal"])
argparser.add_argument("key", type=str)
argparser.add_argument("command", nargs=argparse.REMAINDER)

def execute(args, master, component=None):
    try:
        keyval, mod = Gtk.accelerator_parse(args.key)
    except Exception as e:
        return f"Invalid Keybinding {e}"
    if not keyval:
        return f"Invalid Keybinding {args.key}"
    
    context = None
    if args.scope == "filetree":
        context = master.filetree.binding
    if args.scope == "global":
        context = master.binding
    if args.scope == "editor":
        context = master.editor.binding
    if args.scope == "terminal":
        from components.terminal import Terminal
        context = Terminal.binding
    if context is None:
        return "Context not (yet) supported"

    if args.key in args.command:
        context[args.key] = args.command
        return (f"Replacing keybinding {args.key}:")+" ".join(args.command)
    else:
        context[args.key] = args.command
        return (f"Settings keybinding {args.key}: ")+" ".join(args.command)

register_client_command("kb-set", argparser, execute)

