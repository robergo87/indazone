import os

from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib

from commands._base import execute_command

from components.editor import Editor
from components.terminal import Terminal, TerminalGroup, TerminalAside      
from components.bufferlist import BufferList
from components.filetree import FileTree



def load_css():
    # CSS to set background color
    basedir =  os.path.dirname(os.path.dirname(__file__))
    #with open(os.path.join(basedir, "gtk.css"), "rb") as f:
    #    provider = Gtk.CssProvider()
    #    css = f.read()
    #    provider.load_from_data(css)
    #    Gtk.StyleContext.add_provider_for_screen(
    #        Gdk.Screen.get_default(),
    #        provider,
    #        Gtk.STYLE_PROVIDER_PRIORITY_THEME
    #    )
    with open(os.path.join(basedir, "override.css"), "rb") as f:
        provider = Gtk.CssProvider()
        css = f.read()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class TitleBar(Gtk.EventBox):
    def __init__(self, master, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = master
        self.get_style_context().add_class("titlebar")
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK)
        self.connect("button-press-event", self.on_press)
        self.master.connect("window-state-event", self.on_window_state_event)

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.box.set_border_width(4)
        self.add(self.box)
        self.label = Gtk.Label(label=title)
        self.box.pack_start(self.label, True, True, 0)

        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        self.close_btn = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        self.close_btn.add(close_icon)
        self.close_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.close_btn.connect("clicked", lambda b: self.master.close())
        self.box.pack_end(self.close_btn, False, False, 0)

        self.restore_btn = Gtk.Button()
        self.max_icon = Gtk.Image.new_from_icon_name("window-maximize-symbolic", Gtk.IconSize.BUTTON)
        self.restore_icon = Gtk.Image.new_from_icon_name("window-restore-symbolic", Gtk.IconSize.BUTTON)
        
        self.restore_btn.add(self.max_icon)
        self.restore_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.restore_btn.connect("clicked", self.on_toggle_maximize)
        self.box.pack_end(self.restore_btn, False, False, 0)

        self.min_btn = Gtk.Button()
        min_icon = Gtk.Image.new_from_icon_name("window-minimize-symbolic", Gtk.IconSize.BUTTON)
        self.min_btn.add(min_icon)
        self.min_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.min_btn.connect("clicked", lambda b: self.master.iconify())
        self.box.pack_end(self.min_btn, False, False, 0)

    def on_window_state_event(self, widget, event):
        if self.master.is_maximized():
            self.set_max_icon(self.restore_icon)
        else:
            self.set_max_icon(self.max_icon)

    def set_max_icon(self, icon_widget):
        for child in self.restore_btn.get_children():
            self.restore_btn.remove(child)
        self.restore_btn.add(icon_widget)
        self.restore_btn.show_all()

    def on_toggle_maximize(self, button):
        if self.master.is_maximized():
            self.master.unmaximize()
            self.set_max_icon(self.max_icon)
        else:
            self.master.maximize()
            self.set_max_icon(self.restore_icon)

    def on_press(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            self.on_toggle_maximize(self.restore_btn)
            return True
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self.master.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
        return True

        #titlebar_box.pack_end(close_btn, False, False, 0)



class MasterWindow(Gtk.Window):
    def __init__(self, workdir, sessionid):
        super().__init__(title="GTK3 Code Editor")
        self.workdir = os.path.abspath(workdir)
        self.sessionid = sessionid
        self.set_default_size(1400, 600)

        self.terminal_font_size = 10
        self.terminal_font_family = "Monospace"
        # Put editor inside a scrolled window

        #self.header = Gtk.HeaderBar(title="My Custom Title")
        #self.header.set_show_close_button(True)
        #self.set_titlebar(self.header)
        #self.set_decorated(False)
        self.box_counter = 0
        self.boxes = {}
        self.binding = {}
 
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)
       
        self.titlebar = TitleBar(self, "InDaZone Editor")
        self.vbox.pack_start(self.titlebar, False, False, 0)
        self.set_decorated(False)

        self.master = Gtk.HPaned()
        self.vbox.pack_start(self.master, True, True, 0)

        self.leftmenu = Gtk.VPaned()
        self.master.pack1(self.leftmenu)
        
        self.bufferlist = BufferList(self)
        self.bufferlist.set_vexpand(True) 
        self.leftmenu.pack1(self.bufferlist, resize=False, shrink=False)
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

    def trigger_update_terminal_font(self):
        terminals = self.rightmenu.get_terminals()
        font_desc = Pango.FontDescription(
            f"{self.terminal_font_family} {self.terminal_font_size}"
        )        
        for terminal in terminals:
            terminal.set_font(font_desc)
        return bool(terminals)

    def register_box(self, box):
        self.boxes[self.box_counter] = box
        self.box_counter += 1
        return self.box_counter

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
            x, y = box.translate_coordinates(self, 0, 0)
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
            x, y = box.translate_coordinates(self, 0, 0)
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
            x, y = box.translate_coordinates(self, 0, 0)
            allocation = box.get_allocation()
            x += allocation.width / 2
            y += allocation.height
            print("Candidate", x, y)
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
            x, y = box.translate_coordinates(self, 0, 0)
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
