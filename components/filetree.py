import os
import threading
import shutil

from gi.repository import Gtk, GtkSource, Gdk, Gio, Pango, Vte, GLib, GdkPixbuf
from commands._base import execute_command
#from inotify import INotify, flags

from ._base import DialogYesNo, DialogPrompt


icon_theme = Gtk.IconTheme.get_default()
FOLDER = icon_theme.load_icon("folder", 16, 0)
FOLDER_OPEN = icon_theme.load_icon("folder-open", 16, 0)
FILE = icon_theme.load_icon("text-x-generic", 16, 0)


def isdir(path):
    try:
        return os.path.isdir(path)
    except:
        return False

def exists(path):
    try:
        return os.path.exists(path)
    except:
        return False

def touch(path):
    if exists(path):
        return False
    try:
        with open(path, "w") as f:
            return True
    except:
        return False

def get_chmod(path):
    import stat
    st = os.stat(path)
    return str(oct(stat.S_IMODE(st.st_mode)))[2:]

def set_chmod(path, mode_str):
    mode = int(mode_str, 8)
    os.chmod(path, mode)
    return True
    
def mkdir(path):
    try:
        os.mkdir(path)
        return True
    except:
        return False

def isfile(path):
    try:
        return not os.path.isdir(path)
    except:
        return False

def listdir(path):
    try:
        return os.listdir(path)
    except:
        return []

def rename(path, newpath):
    try:
        os.rename(path, newpath)
        return True
    except:
        return False

def copy(path, newpath):
    if isdir(path):
        try:
            shutil.copytree(path, newpath)
            return True
        except:
            return False
    if isfile(path):
        try:
            shutil.copy(path, newpath)
            return True
        except:
            return False

def unlink(path):
    if isdir(path):
        try:
            shutil.rmtree(path)
            return True
        except:
            return False
    if isfile(path):
        try:
            os.remove(path)
            return True
        except:
            return False



        
class ContextMenu(Gtk.Menu):
    def __init__(self, tree, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = tree

        open_item = Gtk.MenuItem(label="New File")
        open_item.connect("activate", self.on_new_file_item)
        self.append(open_item)

        open_item = Gtk.MenuItem(label="New Directory")
        open_item.connect("activate", self.on_new_dir_item)
        self.append(open_item)

        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self.on_open_item)
        self.append(open_item)

        open_item = Gtk.MenuItem(label="Permissions")
        open_item.connect("activate", self.on_permissions_item)
        self.append(open_item)

        open_item = Gtk.MenuItem(label="Copy")
        open_item.connect("activate", self.on_copy_item)
        self.append(open_item)
        open_item = Gtk.MenuItem(label="Rename")
        open_item.connect("activate", self.on_rename_item)
        self.append(open_item)

        delete_item = Gtk.MenuItem(label="Delete")
        delete_item.connect("activate", self.on_delete_item)
        self.append(delete_item)
        self.show_all()

    def on_new_file_item(self, evt):
        self.tree.trigger_new_file()

    def on_new_dir_item(self, evt):
        self.tree.trigger_new_dir()

    def on_permissions_item(self, evt):
        self.tree.trigger_chmod()

    def on_copy_item(self, evt):
        print("Not implemented")

    def on_rename_item(self, evt):
        self.tree.trigger_rename()

    def on_open_item(self, evt):
        self.tree.trigger_open()

    def on_delete_item(self, evt):
        self.tree.trigger_delete()


class FileTree(Gtk.Box):
    def __init__(self, master, *args, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10, *args, **kwargs)
        self.get_style_context().add_class("unfocused")
        self.master = master        
        self.opened = {}
        self.elements = {}
        self.treestore = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, int, str)

        self.font_family = "Sans"
        self.font_size = 10

        self.sort_model = Gtk.TreeModelSort(model=self.treestore)
        def sort_func(model, iter1, iter2, user_data):
            prio1 = model.get_value(iter1, 2)
            prio2 = model.get_value(iter2, 2)
            if prio1 != prio2:
                return prio1-prio2
            val1 = model.get_value(iter1, 1).lower()
            val2 = model.get_value(iter2, 1).lower()
            return (val1 < val2) - (val1 > val2)
        self.sort_model.set_sort_func(0, sort_func, None)
        self.sort_model.set_sort_column_id(0, Gtk.SortType.DESCENDING)
    
        self.treeview = Gtk.TreeView(model=self.sort_model)
        self.treeview.set_headers_visible(False)
        self.treeview.connect("button-press-event", self.on_button_press)
        self.treeview.set_property("enable-search", False)  # disables type-to-search
        self.treeview.set_activate_on_single_click(False)   # prevents single-click edit

        self.window = Gtk.ScrolledWindow()
        self.pack_start(self.window, expand=True, fill=True, padding=0)
        self.window.add(self.treeview)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        self.renderer_text = Gtk.CellRendererText()

        column = Gtk.TreeViewColumn("Name")
        column.pack_start(renderer_pixbuf, False)   # icon goes first
        column.pack_start(self.renderer_text, True)   # text goes after icon
        column.add_attribute(renderer_pixbuf, "pixbuf", 0)
        column.add_attribute(self.renderer_text, "text", 1)
        self.treeview.append_column(column)

        self.treeview.set_show_expanders(False)
        self.treeview.set_level_indentation(20)
        self.treeview.connect("row-activated", self.on_row_activated)
        self.update_tree()
        self.update_font(now=True)

        self.binding = {}
        self.connect("key-press-event", self.on_key_press)

        self.treeview.set_can_focus(True)
        self.treeview.connect("focus-in-event", self.on_focus_in)
        self.treeview.connect("focus-out-event", self.on_focus_out)

        gio_dir = Gio.File.new_for_path(self.master.workdir)
        self.root_monitor = gio_dir.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        self.root_monitor.connect("changed", self.trigger_update_tree)


    def update_font(self, now=False):
        if now:
            self.renderer_text.set_property("font", f"{self.font_family} {self.font_size}")
            return True
        def inner():
            self.renderer_text.set_property("font", f"{self.font_family} {self.font_size}")
            self.treeview.queue_draw()         
            self.treeview.columns_autosize()
        GLib.idle_add(inner)
        return True

    def grab_focus(self):
        self.treeview.grab_focus()
    
    def on_focus_in(self, widget, event):
        self.get_style_context().remove_class("unfocused")
        self.get_style_context().add_class("focused")

    def on_focus_out(self, widget, event):
        self.get_style_context().remove_class("focused")
        self.get_style_context().add_class("unfocused")
    

    def on_key_press(self, widget, event):
        keyval, mods = event.keyval, event.state & Gtk.accelerator_get_default_mod_mask()
        keyname = Gtk.accelerator_name(keyval, mods)
        if keyval == Gdk.KEY_Menu:
            menu = ContextMenu(self)
            menu.popup_at_pointer(None)             
        if keyname in self.binding:
            try:
                execute_command(
                    self.binding[keyname], client=True, master=self.master
                )
            except SystemExit as e:
                pass
            return True
        return False

    def get_current_path(self):
        selection = self.treeview.get_selection()
        model, tree_iter = selection.get_selected()
        return model[tree_iter][3]

    def trigger_update_tree(self, *args, **kwargs):
        print("TRIGGER UPDATE")
        GLib.idle_add(self.update_tree)
    
    def trigger_open(self):
        currpath = self.get_current_path()
        fullpath = os.path.join(self.master.workdir,currpath)
        if isdir(fullpath):
            if currpath in self.opened:
                #self.inotify.rm_watch(self.opened[currpath])
                self.opened[currpath].cancel()
                del self.opened[currpath]
            else:
                gio_dir = Gio.File.new_for_path(fullpath)
                monitor = gio_dir.monitor_directory(Gio.FileMonitorFlags.NONE, None)
                monitor.connect("changed", self.trigger_update_tree)
                self.opened[currpath] = monitor
                #self.opened[currpath] = self.inotify.add_watch(fullpath, self.watch_flags)
            self.trigger_update_tree()
        else:
            self.master.editor.trigger_open(currpath)

    def trigger_force_delete(self):
        currpath = self.get_current_path()
        fullpath = os.path.join(self.master.workdir,currpath)
        unlink(fullpath)

    def new_file_or_dir(self, isnewdir=False):
        currpath = self.get_current_path()
        fullpath = os.path.join(self.master.workdir,currpath)
        if isfile(fullpath):
            currpath = os.path.dirname(currpath)
        restype = "directory" if isnewdir else "file"
        dialog = DialogPrompt(
            parent=self.master,
            message=f"Create new {restype} in {currpath}" if currpath else f"Create new {restype}",
            defval=""
        )
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        newfile = dialog.get_text()
        if not newfile:
            dialog.destroy()
            return            
        newpath = os.path.join(self.master.workdir, currpath, newfile)
        if isnewdir:
            mkdir(newpath)
        else:
            touch(newpath)
        dialog.destroy()
        self.trigger_update_tree()

    def trigger_new_file(self):
        return self.new_file_or_dir()

    def trigger_new_dir(self):
        return self.new_file_or_dir(True)
        

    def trigger_copy(self):
        currpath = self.get_current_path()
        dialog = DialogPrompt(
            parent=self.master,
            message=f"Moving {currpath}",
            defval=currpath
        )
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        fullpath = os.path.join(self.master.workdir,currpath)
        newfile = dialog.get_text()
        if not newfile:
            dialog.destroy()
            return            
        newpath = os.path.join(self.master.workdir, newfile)
        copy(fullpath, newpath)
        dialog.destroy()
        self.trigger_update_tree()

    def trigger_chmod(self):
        currpath = self.get_current_path()
        fullpath = os.path.join(self.master.workdir,currpath)
        dialog = DialogPrompt(
            parent=self.master,
            message=f"Moving {currpath}",
            defval=get_chmod(fullpath)
        )
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        fullpath = os.path.join(self.master.workdir,currpath)
        newchmod = dialog.get_text()
        if not newchmod:
            dialog.destroy()
            return            
        set_chmod(fullpath, newchmod)
        dialog.destroy()
        self.trigger_update_tree()
        
    def trigger_rename(self):
        currpath = self.get_current_path()
        dialog = DialogPrompt(
            parent=self.master,
            message=f"Moving {currpath}",
            defval=currpath
        )
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        fullpath = os.path.join(self.master.workdir,currpath)
        newfile = dialog.get_text()
        if not newfile:
            dialog.destroy()
            return            
        newpath = os.path.join(self.master.workdir, newfile)
        rename(fullpath, newpath)
        dialog.destroy()
        self.trigger_update_tree()

    def trigger_delete(self):
        currpath = self.get_current_path()
        dialog = DialogYesNo(
            parent=self.master,
            message=f"Remove {currpath}?",
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            self.trigger_force_delete()
        dialog.destroy()
        self.trigger_update_tree()

    def on_button_press(self, widget, event):
        if event.type != Gdk.EventType.BUTTON_PRESS or event.button != 3: 
            return False
        path_info = self.treeview.get_path_at_pos(int(event.x), int(event.y))
        if path_info is None:
            return False
        path, col, cellx, celly = path_info
        self.treeview.grab_focus()
        self.treeview.set_cursor(path, col, 0)
        
        menu = ContextMenu(self)
        menu.popup_at_pointer(event) 

    def on_row_activated(self, treeview, path, column):
        self.trigger_open()
        return True


    def iterate_children(self, parent):
        child = self.treestore.iter_children(parent)
        while child:
            yield child
            for subchild in self.iterate_children(child):
                yield subchild
            child = self.treestore.iter_next(child)

    def iterate_tree(self):
        iter_ = self.treestore.get_iter_first()
        while iter_:
            yield iter_
            # descend into children
            for child in self.iterate_children(iter_):
                yield child
            iter_ = self.treestore.iter_next(iter_)

    def get_dir_contents(self, basedir, dirpath):
        retval = {}

        fulldirpath = os.path.join(basedir, dirpath) if dirpath else basedir
        try:
            files = listdir(fulldirpath)
        except Exception as e:
            files = []
            raise e
        files.sort()
        for filename in files:
            if filename in (".", ".."):
                continue
            currpath = os.path.join(dirpath, filename) if dirpath else filename
            fullcurrpath = os.path.join(basedir, currpath)
            is_dir = 1 if os.path.isdir(fullcurrpath) else 0
            retval[currpath] = {
                "is_dir": is_dir,
                "filename": filename,
                "path": currpath,
                "parent": dirpath
            }
        return retval

    def update_tree(self):
        basedir = self.master.workdir
        contents = self.get_dir_contents(basedir, None)
        for dirpath in self.opened:
            contents |= self.get_dir_contents(basedir, dirpath)

        parents = {}
        to_remove = []
        for node in list(self.iterate_tree()):
            is_dir = self.treestore.get_value(node, 2)
            currpath = self.treestore.get_value(node, 3)
            if currpath not in contents:
                print("removing", currpath, flush=True)
                to_remove.append(node)
                if currpath in self.opened:
                    self.opened[currpath].cancel()
                    del self.opened[currpath]
                continue
            if is_dir:
                parents[currpath] = node
            del contents[currpath]
        for node in to_remove[::-1]:
            self.treestore.remove(node)

        for row in contents.values():
            print("adding", row["path"])
            if row["parent"]:
                if row["parent"] not in parents:
                    continue
                parent = parents[row["parent"]]
            else:
                parent = None
            fullcurrpath = os.path.join(basedir, row["path"])
            if row["is_dir"]:
                icon = FOLDER_OPEN if row["path"] in self.opened else FOLDER
            else:
                icon = FILE
            treestore_row = [icon , "  "+row["filename"], row["is_dir"], row["path"]]
            self.treestore.append(parent, treestore_row)
        self.treeview.expand_all()

