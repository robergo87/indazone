import os

from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from commands._base import execute_command

TERMINAL_PALETTE = [
    Gdk.RGBA(0.18, 0.20, 0.21, 1),  # Black
    Gdk.RGBA(0.80, 0.00, 0.00, 1),  # Red
    Gdk.RGBA(0.31, 0.61, 0.02, 1),  # Green
    Gdk.RGBA(0.77, 0.63, 0.00, 1),  # Yellow
    Gdk.RGBA(0.20, 0.40, 0.64, 1),  # Blue
    Gdk.RGBA(0.46, 0.31, 0.48, 1),  # Magenta
    Gdk.RGBA(0.02, 0.60, 0.60, 1),  # Cyan
    Gdk.RGBA(0.82, 0.85, 0.81, 1),  # White
    Gdk.RGBA(0.33, 0.33, 0.33, 1),  # Bright Black
    Gdk.RGBA(0.94, 0.16, 0.16, 1),  # Bright Red
    Gdk.RGBA(0.54, 0.89, 0.20, 1),  # Bright Green
    Gdk.RGBA(0.99, 0.91, 0.31, 1),  # Bright Yellow
    Gdk.RGBA(0.45, 0.62, 0.81, 1),  # Bright Blue
    Gdk.RGBA(0.68, 0.50, 0.66, 1),  # Bright Magenta
    Gdk.RGBA(0.20, 0.88, 0.88, 1),  # Bright Cyan
    Gdk.RGBA(0.93, 0.93, 0.93, 1)   # Bright White
]
        
class Terminal(Vte.Terminal):
    def __init__(self, master, group):
        super().__init__()
        self.master = master
        self.group = group
        self._spawned = False
        self.pos = -1
        #self.set_clear_background(False)

        font_desc = Pango.FontDescription(
            f"{master.terminal_font_family} {master.terminal_font_size}"
        )
        self.set_font(font_desc)
        self.set_allow_bold(True)
        self.set_bold_is_bright(True)
        self.set_hexpand(True)   # allow horizontal expansion
        self.set_vexpand(True)
        
        # Tango pallete
        self.set_colors(None, None, TERMINAL_PALETTE)
        self.set_scroll_on_output(True)
        self.set_scroll_on_keystroke(True)

        self.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        
        self.connect("realize", self._on_realize)
        self.connect("focus-in-event", self.group.on_focus_in)
        self.connect("focus-out-event", self.group.on_focus_out)        
        self.connect("key-press-event", self.on_key_press)
        self.connect("child-exited", self.on_child_exited)
        self.connect("size-allocate", self.on_size_allocate)

    def get_font_cell_size(self):
        desc = self.get_font()
        layout = self.create_pango_layout("W")
        layout.set_font_description(desc)
        width, height = layout.get_pixel_size()
        return width, height
    
    def on_size_allocate(self, widget, allocation):
        """Update the PTY size to match the terminal widget size."""
        char_width, char_height = self.get_font_cell_size()
        if char_width > 0 and char_height > 0:
            cols = max(1, allocation.width // char_width)
            rows = max(1, allocation.height // char_height)
            self.set_size(cols, rows)
            
    def set_pos(self, pos):
        self.pos = pos

    def on_child_exited(self, terminal, status):
        self.group.terminal_closed(self.pos)

    def _on_realize(self, *args, **kwargs):
        envv = (
            [f"{k}={v}" for k, v in dict(os.environ).items()] +
            ["TERM=xterm-256color", f"IDZ={self.master.sessionid}"]
        )
        self.spawn_async(
            pty_flags=Vte.PtyFlags.DEFAULT,
            working_directory=None, 
            argv=['/bin/bash', '-i'],
            envv=envv,
            spawn_flags=GLib.SpawnFlags.DEFAULT, 
            child_setup=None,
            child_setup_data=None,
            timeout=-1
        )


    def on_key_press(self, widget, event):
        keyval, mods = event.keyval, event.state & Gtk.accelerator_get_default_mod_mask()
        keyname = Gtk.accelerator_name(keyval, mods)
        if keyname == "<Primary><Shift>c" or keyname == "<Control><Shift>c":
            self.copy_clipboard()
            return True
        if keyname == "<Primary><Shift>v" or keyname == "<Control><Shift>v":
            self.paste_clipboard()
            return True
        if keyval == Gdk.KEY_Menu:
            menu = ContextMenu(self)
            menu.popup_at_pointer(None)          
        if keyname in Terminal.binding:
            try:
                execute_command(
                    Terminal.binding[keyname], client=True, master=self.master, component=self
                )
            except SystemExit as e:
                pass
            return True
        return False

Terminal.binding = {}

class TerminalGroup(Gtk.Box):
    def __init__(self, master):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.master = master
        self.box_id = master.register_box(self)
        self.get_style_context().add_class("unfocused")

        self.counter = 0
        self.terminals = {}
        self.terminal_list = []
        self.current_terminal = None
        
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.add(self.notebook)
        self.spawn_terminal()

    def get_terminals(self):
        return list(self.terminals.values())

    def set_pos(self, prnt, pos):
        self.pos = pos
        self.prnt = prnt

    def terminal_closed(self, pos):
        index = self.terminal_list.index(pos)
        if index:
            self.current_terminal = self.terminal_list[index-1]
        elif len(self.terminal_list) == 1:
            self.current_terminal = None
        self.notebook.remove_page(index)
        del self.terminals[pos]
        self.terminal_list.remove(pos)
        if not self.terminal_list:
            self.prnt.move_focus()
            self.master.remove_box(self.box_id)
            self.prnt.collapse(self.pos)
            self.master.focus_box(list(self.master.boxes)[-1])

    def get_current_terminal(self):
        if self.current_terminal is None:
            return None
        return self.terminals[self.current_terminal]

    def spawn_terminal(self):
        terminal = Terminal(self.master, self)
        self.terminals[self.counter] = terminal
        self.notebook.append_page(terminal, Gtk.Label(label=f"Term {self.counter}"))
        terminal.show_all()
        terminal.set_pos(self.counter)
        if self.current_terminal is None:
            self.current_terminal = self.counter
        self.terminal_list.append(self.counter)
        self.counter += 1

    def grab_focus(self, term_no=None):
        if term_no and termno in self.terminals:
            terminal = self.terminals[term_no]
        else:
            terminal = self.get_current_terminal()
        if terminal:
            GLib.idle_add(terminal.grab_focus)

    def has_focus(self):
        self.get_style_context().has_class("unfocused")

    def on_focus_in(self, widget, event):
        self.get_style_context().remove_class("unfocused")
        self.get_style_context().add_class("focused")

    def on_focus_out(self, widget, event):
        self.get_style_context().remove_class("focused")
        self.get_style_context().add_class("unfocused")


    def trigger_open(self, focus=False):
        self.spawn_terminal()
        if focus:
            self.grab_focus()
        return self.counter-1

    def trigger_split(self):
        self.prnt.split(self.pos)
        self.master.focus_box(self.box_id)
    
    def trigger_close(self):
        if self.current_terminal is None:
            return False
        if self.current_terminal not in self.terminal_list:
            return False
        if len(self.terminal_list) <= 1:
            return False
        page_num = self.terminal_list.index(self.current_terminal)
        to_remove = self.current_terminal
        if page_num == 0:
            self.current_terminal = self.terminal_list[page_num+1]
        else:
            self.current_terminal = self.terminal_list[page_num-1]
        self.terminal_list.remove(to_remove)
        del self.terminals[to_remove]
        self.notebook.remove_page(page_num)
        return True

    def trigger_prev(self, focus):
        if self.current_terminal is None:
            return False
        if self.current_terminal not in self.terminal_list:
            return False
        page_num = self.terminal_list.index(self.current_terminal)
        if page_num == 0:
            return False    
        self.notebook.set_current_page(page_num-1)
        self.current_terminal = self.terminal_list[page_num-1]
        if focus:
            self.grab_focus()
        return True

    def trigger_next(self, focus):
        if self.current_terminal is None:
            return False
        if self.current_terminal not in self.terminal_list:
            return False
        page_num = self.terminal_list.index(self.current_terminal)
        if page_num == len(self.terminal_list)-1:
            print("Last terminal")
            return False    
        self.notebook.set_current_page(page_num+1)
        self.current_terminal = self.terminal_list[page_num+1]
        if focus:
            self.grab_focus()
        return True


class TerminalSplit(Gtk.VPaned):
    def __init__(self, master, tgroup):
        super().__init__()
        self.master = master
        self.prnt = None
        self.pos = -1

        self.top_group = None
        self.replace(1, tgroup)
        self.bottom_group = None
        self.replace(2, TerminalGroup(master))

    
    def get_terminals(self):
        return (
            (self.top_group.get_terminals() if self.top_group else [])
            +
            (self.bottom_group.get_terminals() if self.bottom_group else [])
        )

    def move_focus(self):
        self.master.trigger_focus_up()

    def set_pos(self, prnt, pos):
        self.pos = pos
        self.prnt = prnt

    def split(self, index):
        position = self.get_position()
        if index == 1:
            item = self.top_group
        else:
            item = self.bottom_group
        self.remove(item)
        tgroup = TerminalSplit(self.master, item)
        self.replace(index, tgroup)
        self.set_position(position)
        
    def replace(self, index, item):
        if index == 1:
            if self.top_group:
                self.remove(self.top_group)
            self.top_group = item
            self.pack1(self.top_group, resize=True, shrink=True)
            self.top_group.set_pos(self, 1)
            self.top_group.show_all()
        else:
            if self.bottom_group:
                self.remove(self.bottom_group)
            self.bottom_group = item
            self.pack2(self.bottom_group, resize=True, shrink=True)
            self.bottom_group.set_pos(self, 2)
            self.bottom_group.show_all()
    
    def collapse(self, index):
        if index == 1:
            self.remove(self.bottom_group)
            self.prnt.replace(self.pos, self.bottom_group)
        else:
            self.remove(self.top_group)
            self.prnt.replace(self.pos, self.top_group)
        

class TerminalAside(Gtk.Box):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.content = None
        self.replace(1, TerminalGroup(master))

    def get_terminals(self):
        if self.content:
            return self.content.get_terminals()
        
    def split(self, index):
        self.remove(self.content)
        tgroup = TerminalSplit(self.master, self.content)
        self.replace(1, tgroup)

    def replace(self, index, item):
        if self.content:
            self.remove(self.content)
        self.content = item
        self.add(self.content)
        self.content.set_pos(self, 1)
        self.content.show_all()
        
    def collapse(self, index):
        self.replace(1, TerminalGroup(self.master))

    def move_focus(self):
        self.master.trigger_focus_left()

