from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from components.master import MasterWindow, load_css
from commands._base import CommandParser, register_client_command

from gi.repository import Pango, PangoCairo

def get_fonts():
    fontmap = PangoCairo.font_map_get_default()
    return [
        fam.get_name() for fam in fontmap.list_families() if fam.is_monospace()
    ]

argparser = CommandParser("editor")
argparser.add_argument("command", type=str, choices=[
    "fonts", "font-inc", "font-dec"
])
def execute(args, master, component=None):
    if args.command == "fonts":
        return get_fonts()
    if args.command == "font-inc":
        master.editor.font_size +=1
        return master.editor.trigger_update_font()
    if args.command == "font-dec":
        master.editor.font_size -=1
        return master.editor.trigger_update_font()
    return False
register_client_command("editor", argparser, execute)


argparser = CommandParser("set-editor-font-family")
argparser.add_argument("family", type=str, choices=get_fonts())
def execute(args, master, component=None):
    master.editor.font_family = args.family
    return master.editor.trigger_update_font()
register_client_command("set-editor-font-family", argparser, execute)


argparser = CommandParser("set-editor-font-size")
argparser.add_argument("size", type=int)
def execute(args, master, component=None):
    master.editor.font_size = args.size
    return master.editor.trigger_update_font()
register_client_command("set-editor-font-size", argparser, execute)



argparser = CommandParser("editor-search-window")
def execute(args, master, component=None):
    return master.editor.trigger_search_window()
register_client_command("editor-search-window", argparser, execute)

argparser = CommandParser("editor-search")
argparser.add_argument("phrase", type=str)
def execute(args, master, component=None):
    return master.editor.trigger_search(phrase=args.phrase)
register_client_command("editor-search", argparser, execute)

argparser = CommandParser("editor-search-next")
def execute(args, master, component=None):
    return master.editor.trigger_search(last=True)
register_client_command("editor-search-next", argparser, execute)



argparser = CommandParser("editor-go-to-line-window")
def execute(args, master, component=None):
    return master.editor.trigger_go_to_line_window()
register_client_command("editor-go-to-line-window", argparser, execute)

argparser = CommandParser("editor-go-to-line")
argparser.add_argument("lineno", type=int)
def execute(args, master, component=None):
    return master.editor.trigger_go_to_line(args.lineno)
register_client_command("editor-go-to-line", argparser, execute)

