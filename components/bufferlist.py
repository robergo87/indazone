import os

from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib


class BufferList(Gtk.Box):
    def __init__(self, master, *args, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10, *args, **kwargs)
        self.get_style_context().add_class("unfocused")

        self.master = master
        self.liststore = Gtk.ListStore(str, str, str, Gdk.RGBA)
        self.buffer_mapping = {}   
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_headers_visible(False)

        self.window = Gtk.ScrolledWindow()
        self.pack_start(self.window, expand=True, fill=True, padding=0)
        #self.window.add(self.treeview)
        self.pack_start(self.treeview, expand=False, fill=True, padding=0)
        
        # Add a text column
        renderer = Gtk.CellRendererText()
        renderer.set_property("foreground-set", True)
    
        column = Gtk.TreeViewColumn("Flag", renderer, text=0)
        column.add_attribute(renderer, "foreground-rgba", 3)
        self.treeview.append_column(column)

        column = Gtk.TreeViewColumn("Label", renderer, text=1)
        column.add_attribute(renderer, "foreground-rgba", 3)
        self.treeview.append_column(column)
        

        self.sort_model = Gtk.TreeModelSort(model=self.liststore)
        def sort_func(model, iter1, iter2, user_data):
            try:
                index1 = self.master.editor.buffer_list.index(model.get_value(iter1, 2))
            except ValueError:
                index1 = -1
            try:
                index2 = self.master.editor.buffer_list.index(model.get_value(iter2, 2))
            except ValueError:
                index2 = -1
            if index1 == index2:
                return 0
            return 1 if index1 > index2 else -1
        self.sort_model.set_sort_func(0, sort_func, None)
        self.sort_model.set_sort_column_id(0, Gtk.SortType.ASCENDING)


        self.selection = self.treeview.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.selection.connect("changed", self.on_selection_changed)
        self.treeview.connect("row-activated", self.on_row_activated)

        self.treeview.set_can_focus(True)
        self.treeview.connect("focus-in-event", self.on_focus_in)
        self.treeview.connect("focus-out-event", self.on_focus_out)

    def grab_focus(self):
        self.treeview.grab_focus()

    def on_focus_in(self, widget, event):
        self.get_style_context().remove_class("unfocused")
        self.get_style_context().add_class("focused")

    def on_focus_out(self, widget, event):
        self.get_style_context().remove_class("focused")
        self.get_style_context().add_class("unfocused")

    def get_current_path(self):
        selection = self.treeview.get_selection()
        model, tree_iter = selection.get_selected()
        return model[tree_iter][2]

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            self.master.editor.trigger_focus(model[treeiter][2], bubble=False)
            
    def on_row_activated(self, treeview, path, column):
        selection = self.treeview.get_selection()
        model, tree_iter = selection.get_selected()
        self.master.editor.trigger_focus(model[tree_iter][2], bubble=False)

    def update_buffers(self):
        editor = self.master.editor
        for filepath in self.buffer_mapping:
            self.buffer_mapping[filepath]["exists"] = False
        for filepath in editor.buffer_list:
            mode = editor.buffers[filepath]["mode"]
            flag = "-"
            color = Gdk.RGBA(0.82, 0.85, 0.81, 1),
            if mode == "saved":
                color = Gdk.RGBA(0.54, 0.89, 0.20, 1)
                flag = "S"
            if mode == "modified":
                color = Gdk.RGBA(0.45, 0.62, 0.81, 1)
                flag = "M"
            if filepath in self.buffer_mapping:
                self.buffer_mapping[filepath]["exists"] = True
                if mode != self.buffer_mapping[filepath]:
                    self.buffer_mapping[filepath]["mode"] = mode
                    self.liststore.set_value(self.buffer_mapping[filepath]["item"], 0, flag)
                    self.liststore.set_value(self.buffer_mapping[filepath]["item"], 3, color)
                continue
            basedir = os.path.basename(os.path.dirname(filepath))
            label = "{}{}{}".format(
                basedir,
                "/" if basedir else "",
                os.path.basename(filepath)
            )
            self.buffer_mapping[filepath] = {
                "exists": True,
                "mode": mode,
                "item": self.liststore.append([flag, label, filepath, color])
            }
        for filepath in list(self.buffer_mapping):
            if self.buffer_mapping[filepath]["exists"]:
                continue
            self.liststore.remove(self.buffer_mapping[filepath]["item"])
            del self.buffer_mapping[filepath]
        if editor.current_buffer in editor.buffer_list:
            index = editor.buffer_list.index(editor.current_buffer)
            selection = self.treeview.get_selection()
            selection.unselect_all()
            selection.select_path(index)
