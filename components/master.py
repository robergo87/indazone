import os

from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from commands._base import execute_command

from components.editor import Editor
from components.terminal import Terminal, TerminalGroup, TerminalAside      
from components.bufferlist import BufferList
from components.filetree import FileTree



def load_css():
    # CSS to set background color
    css = b"""
    treeview {
        background-color: #272d2f;
        color: #ccc;
    }
    treeview:selected, treeview:selected:focus {
        background: #475254;
        color: inherit; 
        font-weight: bold;
    }
    box.unfocused {
        background-color: #272d2f;
        border: 2px dotted #888888;
        padding: 3px;
        margin: 3px;
    }
    box.focused {
        background-color: #272d2f;
        border: 2px dotted #ffffff;
        padding: 3px;
        margin: 3px;
    }
    terminal, notebook terminal {
        background-color: #272d2f;
    }
    notebook {
        border: 2px solid #555;
        background-color: #333;
    }
    notebook > header {
        background-color: #333;
        font-size: 8px;
    }
    notebook > header tab {
        background-color: #272d2f;
        font-size: 10px;
        padding: 2px 10px;
        margin: 0 1px;
        color: #ccc;
        border-color: #aaa;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }

    notebook > header tab:selected, notebook > header tab:checked  {
        color: white;
        font-weight: bold;
    }
    window {
        background-color: #2e3436;
    }
    headerbar {
        background-color: #111;
        color: #ccc;
        padding: 2px 20px;
        font-size: 10px;
    }
    paned > separator {
        border-style: none;
        background-color: #272d2f;
        min-height: 2px;
        min-width: 2px;
    }
        
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class MasterWindow(Gtk.Window):
    def __init__(self, workdir):
        super().__init__(title="GTK3 Code Editor")
        self.workdir = os.path.abspath(workdir)
        self.set_default_size(1400, 600)

        # Put editor inside a scrolled window

        self.header = Gtk.HeaderBar(title="My Custom Title")
        self.header.set_show_close_button(True)
        self.set_titlebar(self.header)

        self.box_counter = 0
        self.boxes = {}
        self.binding = {}
        
        self.master = Gtk.HPaned()
        self.add(self.master)

        self.leftmenu = Gtk.VPaned()
        self.master.pack1(self.leftmenu)
        
        self.bufferlist = BufferList(self)
        self.leftmenu.pack1(self.bufferlist, resize=True, shrink=True)
        self.register_box(self.bufferlist)
        #self.bufferlist.set_vexpand(True)

        self.filetree = FileTree(self)
        self.leftmenu.pack2(self.filetree, resize=True, shrink=True)
        self.filetree.set_vexpand(True)
        self.register_box(self.filetree)

        self.main_content = Gtk.HPaned()
        self.master.pack2(self.main_content)

        self.editor = Editor(self)
        self.register_box(self.editor)
        self.main_content.pack1(self.editor, resize=True, shrink=True)

        self.rightmenu = TerminalAside(self)
        self.main_content.pack2(self.rightmenu, resize=True, shrink=True)
        

        self.master.set_position(250)
        self.main_content.set_position(600)
        self.show_all()
        self.connect("key-press-event", self.on_key_press)

        self.filetree.grab_focus()

    def register_box(self, box):
        self.boxes[self.box_counter] = box
        self.box_counter += 1
        return self.box_counter-1

    def remove_box(self, boxid):
       if boxid in self.boxes: 
            del self.boxes[boxid]
            
    def on_key_press(self, widget, event):
        keyval, mods = event.keyval, event.state & Gtk.accelerator_get_default_mod_mask()
        keyname = Gtk.accelerator_name(keyval, mods)
        if keyval == Gdk.KEY_Menu:
            menu = ContextMenu(self)
            menu.popup_at_pointer(None)             
        if keyname in self.binding:
            try:
                execute_command(
                    self.binding[keyname], client=True, master=self
                )
            except SystemExit as e:
                pass
            return True
        return False

    def get_current_box(self):
        for box in self.boxes.values():
            if box.get_style_context().has_class("focused"):
                return box
        return None

    def focus_box(self, boxid):
        self.boxes[boxid].grab_focus()
        
    def trigger_focus_left(self):
        current_box = self.get_current_box()
        if not current_box:
            return False
        current_x, current_y = current_box.translate_coordinates(self, 0, 0)
        current_y += current_box.get_allocation().height / 2

        next_box = None
        next_box_dist = -1
        for box in self.boxes.values():
            if box.get_style_context().has_class("focused"):
                continue
            coords = box.translate_coordinates(self, 0, 0)
            if not coords:
                continue
            x, y = coords
            allocation = box.get_allocation()
            x += allocation.width
            y += allocation.height / 2
            if x > current_x:
                continue
            dist = (current_x - x)**2 + (current_y - y)**2
            if dist < next_box_dist or not next_box:
                next_box_dist = dist
                next_box = box
        if not next_box:
            return False
        next_box.grab_focus()
        return True

    def trigger_focus_right(self):
        current_box = self.get_current_box()
        if not current_box:
            return False
        current_x, current_y = current_box.translate_coordinates(self, 0, 0)
        current_x += current_box.get_allocation().width
        current_y += current_box.get_allocation().height / 2

        next_box = None
        next_box_dist = -1
        for box in self.boxes.values():
            if box.get_style_context().has_class("focused"):
                continue
            coords = box.translate_coordinates(self, 0, 0)
            if not coords:
                continue
            x, y = coords
            allocation = box.get_allocation()
            y += allocation.height / 2
            if x < current_x:
                continue
            dist = (current_x - x)**2 + (current_y - y)**2
            if dist < next_box_dist or not next_box:
                next_box_dist = dist
                next_box = box
        if not next_box:
            return False
        next_box.grab_focus()
        return True
        
    def trigger_focus_up(self):
        current_box = self.get_current_box()
        if not current_box:
            return False
        current_x, current_y = current_box.translate_coordinates(self, 0, 0)
        current_x += current_box.get_allocation().width / 2
        next_box = None
        next_box_dist = -1
        for box in self.boxes.values():
            if box.get_style_context().has_class("focused"):
                continue
            coords = box.translate_coordinates(self, 0, 0)
            if not coords:
                continue
            x, y = coords
            allocation = box.get_allocation()
            x += allocation.width / 2
            y += allocation.height
            if y > current_y:
                continue
            dist = (current_x - x)**2 + (current_y - y)**2
            if dist < next_box_dist or not next_box:
                next_box_dist = dist
                next_box = box
        if not next_box:
            return False
        next_box.grab_focus()
        return True

    def trigger_focus_down(self):
        current_box = self.get_current_box()
        if not current_box:
            return False
        current_x, current_y = current_box.translate_coordinates(self, 0, 0)
        current_x += current_box.get_allocation().width / 2
        current_y += current_box.get_allocation().height
        next_box = None
        next_box_dist = -1
        for box in self.boxes.values():
            if box.get_style_context().has_class("focused"):
                continue
            coords = box.translate_coordinates(self, 0, 0)
            if not coords:
                continue
            x, y = coords
            allocation = box.get_allocation()
            x += allocation.width / 2
            if y < current_y:
                continue
            dist = (current_x - x)**2 + (current_y - y)**2
            if dist < next_box_dist or not next_box:
                next_box_dist = dist
                next_box = box
        if not next_box:
            return False
        next_box.grab_focus()
        return True
