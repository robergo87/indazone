from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib, GdkPixbuf

class DialogYesNo(Gtk.Dialog):
    def __init__(self, parent, message):
        super().__init__(title="Confirm", transient_for=parent, modal=True)

        self.set_default_size(200, 100)

        # Content area
        box = self.get_content_area()
        label = Gtk.Label(label=message)
        box.add(label)

        # Add buttons
        self.add_button("Yes", Gtk.ResponseType.YES)
        self.add_button("No", Gtk.ResponseType.NO)

        self.show_all()


class DialogPrompt(Gtk.Dialog):
    def __init__(self, parent, message="Enter text:", defval=""):
        super().__init__(title="Input", transient_for=parent, modal=True)
        self.set_default_size(300, 100)
        box = self.get_content_area()
        label = Gtk.Label(label=message)
        box.add(label)
        self.entry = Gtk.Entry()
        self.entry.set_text(defval)
        box.add(self.entry)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("OK", Gtk.ResponseType.OK)
        self.entry.connect("activate", self.on_entry_activate)
        self.show_all()

    def get_text(self):
        return self.entry.get_text()
        
    def on_entry_activate(self, entry):
        self.response(Gtk.ResponseType.OK)
