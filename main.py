#!/usr/bin/env python3
import sys
import json
import os
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("Vte", "2.91")
gi.require_version("PangoCairo", "1.0")

from commands._base import execute_command
from cli._base import exec_cli


def start_imports():
    import pkgutil
    import importlib

    currdir = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    for loader, name, ispkg in pkgutil.walk_packages(["commands"]):
        if name[0] == "_":
            continue
        importlib.import_module(f"commands.{name}")

    for loader, name, ispkg in pkgutil.walk_packages(["cli"]):
        if name[0] == "_":
            continue
        importlib.import_module(f"cli.{name}")
    os.chdir(currdir)
    
if __name__ == "__main__":
    start_imports()
    exec_cli()
    success, content = execute_command(sys.argv[1:])
    if not success:
        print("ERROR:")
        print(content)
        exit()
    if isinstance(content, str):
        print(content)
    else:
        print(json.dumps(content))
