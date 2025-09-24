import os
import re
import rlcompleter

from gi.repository import Gtk, GtkSource, Gdk, Pango, Vte, GLib, GObject
from commands._base import execute_command

from ._base import DialogPrompt


class PythonProvider(GObject.Object, GtkSource.CompletionProvider):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor

    def do_get_name(self):
        return "rlcompleter"

    def do_match(self, context):
        if self.editor.current_buffer not in self.editor.buffers:
            return False
        buffer = self.editor.buffers[self.editor.current_buffer]["buffer"]
        cursor_iter = buffer.get_iter_at_mark(buffer.get_insert())
        line_start_iter = cursor_iter.copy()
        line_start_iter.set_line_offset(0)
        text_to_cursor = buffer.get_text(line_start_iter, cursor_iter, include_hidden_chars=True)
        if not text_to_cursor.strip():
            return False
        return True

    def do_populate(self, context):
        buffer = self.editor.buffers[self.editor.current_buffer]["buffer"]
        cursor_iter = buffer.get_iter_at_mark(buffer.get_insert())
        code = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        line = cursor_iter.get_line() + 1
        column = cursor_iter.get_line_offset()

        line_start = cursor_iter.copy()
        line_start.set_line_offset(0)
        text_so_far = buffer.get_text(line_start, cursor_iter, True)
        
        try:
            script = jedi.Script(code=code)
            completions = script.complete(line, column)
        except Exception as e:
            completions = []

        # Convert Jedi completions into GtkSource proposals
        proposals = []
        for c in completions:
            print("Compl", [c.name, c.complete]) 
            item = GtkSource.CompletionItem.new(c.name, c.name)
            item.set_info(c.description)
            proposals.append(item)

        context.add_proposals(self, proposals, True)

class KeywordProvider(GObject.GObject, GtkSource.CompletionProvider):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.keywords = set()
        self.buffers = {}

    def do_get_name(self):
        return "Keywords"

    def process_buffer(self, buffer):
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        full_buffer = buffer.get_text(start, end, False)
        return re.findall("[a-zA-Z_][a-zA-Z0-9_][a-zA-Z0-9_]+", full_buffer)


    def set_buffer(self, filename, buffer):
        self.buffers[filename] = self.process_buffer(buffer)
        self.keywords = set()
        for filename, keywords in self.buffers.items():
            self.keywords |= set(keywords)
        
    def unset_buffer(self, filename):
        if filename not in self.buffers:
            return
        del self.buffers[filename]
        self.keywords = []
        for filename, keywords in self.buffers.items():
            self.keywords += keywords

    def do_populate(self, context):
        # Called when completion is requested
        proposals = []
        for kw in self.keywords:
            if kw.startswith(self.last_line):
                proposals.append(GtkSource.CompletionItem.new(kw, kw))
        context.add_proposals(self, proposals, True)


    def do_match(self, context):
        if self.editor.current_buffer not in self.editor.buffers:
            return False
        buffer = self.editor.buffers[self.editor.current_buffer]["buffer"]
        insert_mark = buffer.get_insert()
        iter_at_cursor = buffer.get_iter_at_mark(insert_mark)
        line_start = iter_at_cursor.copy()
        line_start.set_line_offset(0)
        self.last_line = buffer.get_text(line_start, iter_at_cursor, True).strip()
        self.last_line = re.search("[a-zA-Z0-9_]+$", self.last_line)
        if not self.last_line:
            return False
        else: 
            self.last_line = self.last_line[0]
        return len(self.last_line) >= 3

    def do_get_icon(self):
        return None

class Editor(Gtk.Box):
    def __init__(self, master, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.window = Gtk.ScrolledWindow()
        #self.add(self.window)
        self.pack_start(self.window, expand=True, fill=True, padding=0)
        self.get_style_context().add_class("unfocused")
        
        self.binding = {}
        self.buffers = {}
        self.buffer_list = []
        self.current_buffer = None
        self.master = master
        self.search_phrase = None
        
        # Load Python syntax highlighting
        self.default_buffer = GtkSource.Buffer()
        self.lang_manager = GtkSource.LanguageManager()
        self.view = GtkSource.View.new_with_buffer(self.default_buffer)    
        scheme_manager = GtkSource.StyleSchemeManager()
        self.scheme = scheme_manager.get_scheme("oblivion")
        self.default_buffer.set_style_scheme(self.scheme)
        self.default_buffer.set_text("Start")
        
        self.view.set_show_line_numbers(True)
        self.view.set_highlight_current_line(False)

        #provider = PythonProvider(self)
        self.provider = KeywordProvider(self)
        completion = self.view.get_completion()
        completion.add_provider(self.provider)
    
        font_desc = Gtk.Settings.get_default().get_property("gtk-font-name")
        self.font_family = "Monospace"
        self.font_size = 9
        self.trigger_update_font()

        self.view.set_tab_width(4)
        self.view.set_insert_spaces_instead_of_tabs(True)

        self.window.add(self.view)

        self.view.connect("focus-in-event", self.on_focus_in)
        self.view.connect("focus-out-event", self.on_focus_out)

        self.view.connect("key-press-event", self.on_key_press)

    def trigger_search_window(self):
        if self.current_buffer not in self.buffers:
            print("No buffers to search", self.current_buffer)
            return False
        buffer = self.buffers[self.current_buffer]["buffer"]
        phrase = ""
        if selection := buffer.get_selection_bounds():
            text = buffer.get_text(selection[0], selection[1], include_hidden_chars=True)
        dialog = DialogPrompt(
            parent=self.master,
            message=f"Search in file",
            defval=phrase
        )
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return False
        phrase = dialog.get_text()
        dialog.destroy()
        if not phrase:
            return False
        return self.trigger_search(phrase)

    def trigger_search(self, phrase="", last=False):
        if last and not self.search_phrase:
            return False
        if last:
            phrase = self.search_phrase
        else:
            self.search_phrase = phrase
        if self.current_buffer not in self.buffers:
            print("No buffers to search", self.current_buffer)
            return False
        buffer = self.buffers[self.current_buffer]["buffer"]
        if selection := buffer.get_selection_bounds():
            start = selection[1]
        else:
            start = buffer.get_iter_at_mark(buffer.get_insert())
        match = start.forward_search(phrase, 0, None)
        if not match:
            start = buffer.get_start_iter()
            match = start.forward_search(phrase, 0, None)
        if not match:
            print("No match found")
            return False            
        match_start, match_end = match
        self.view.scroll_to_iter(match_end, 0.25, False, 0, 0)
        buffer.select_range(match_start, match_end)
        return True

    def trigger_go_to_line_window(self):
        if self.current_buffer not in self.buffers:
            print("No buffers to search", self.current_buffer)
            return False
        buffer = self.buffers[self.current_buffer]["buffer"]
        dialog = DialogPrompt(
            parent=self.master,
            message=f"Go to line",
            defval=""
        )
        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return False
        lineno = dialog.get_text()
        dialog.destroy()
        if not lineno:
            return False
        return self.trigger_go_to_line(lineno)

    def trigger_go_to_line(self, lineno):
        try:
            lineno = int(lineno)-1
        except:
            return False
        if self.current_buffer not in self.buffers:
            print("No buffers to search", self.current_buffer)
            return False
        buffer = self.buffers[self.current_buffer]["buffer"]
        iter_at_line = buffer.get_iter_at_line(lineno)
        buffer.place_cursor(iter_at_line)
        self.view.scroll_to_iter(iter_at_line, 0.25, use_align=False, xalign=0, yalign=0)
        return True

    def trigger_update_font(self):
        self.view.modify_font(Pango.FontDescription(f"{self.font_family} {self.font_size}"))
        return True

    def on_key_press(self, widget, event):
        keyval, mods = event.keyval, event.state & Gtk.accelerator_get_default_mod_mask()
        keyname = Gtk.accelerator_name(keyval, mods)
        if keyname in self.binding:
            try:
                execute_command(
                    self.binding[keyname], client=True, master=self.master
                )
            except SystemExit as e:
                pass
            return True
        return False
        
    def grab_focus(self):
        self.view.grab_focus()

    def on_focus_in(self, widget, event):
        self.get_style_context().remove_class("unfocused")
        self.get_style_context().add_class("focused")

    def on_focus_out(self, widget, event):
        self.get_style_context().remove_class("focused")
        self.get_style_context().add_class("unfocused")
        
    def trigger_prev(self):
        if self.current_buffer in self.buffer_list:
            index = self.buffer_list.index(self.current_buffer)
        else:
            index = 0
        index -= 1
        index = max(0, index)
        filepath = self.buffer_list[index]
        self.trigger_focus(filepath)

    def trigger_next(self):
        if self.current_buffer in self.buffer_list:
            index = self.buffer_list.index(self.current_buffer)
        else:
            index = -1
        index += 1
        index = min(len(self.buffer_list)-1, index)
        filepath = self.buffer_list[index]
        self.trigger_focus(filepath)

    def trigger_first(self):
        if self.buffer_list:
            self.trigger_focus(self.buffer_list[0])
            return True
        return False

    def trigger_last(self):
        if self.buffer_list:
            self.trigger_focus(self.buffer_list[-1])
            return True
        return False

    def trigger_focus(self, filepath, bubble=True):
        if filepath not in self.buffers:
            return False
        buffer_data = self.buffers[filepath]
        self.view.set_buffer(buffer_data["buffer"])
        self.view.set_tab_width(buffer_data["tab_width"])
        self.view.set_insert_spaces_instead_of_tabs(buffer_data["spaces_to_tabs"])
        self.current_buffer = filepath
        self.grab_focus()
        if bubble:
            self.master.bufferlist.update_buffers()
        return True

    def trigger_save(self, filepath):
        if filepath not in self.buffers:
            return False
        buffer = self.buffers[filepath]["buffer"]
        fullpath = os.path.join(self.master.workdir, filepath)
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        content = buffer.get_text(start_iter, end_iter, include_hidden_chars=True)
        try:
            with open(fullpath, "w") as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing file {fullpath}: {e}")
            return False
        self.buffers[filepath]["mode"] = "saved"
        print(f"Saved {fullpath}")
        self.master.bufferlist.update_buffers()
        return True        
    
    def trigger_close(self, filepath):
        if filepath not in self.buffer_list:
            return False
        self.provider.unset_buffer(filepath)
        if filepath == self.current_buffer:
            index = self.buffer_list.index(filepath)
            if index > 0:
                index -= 1
            if len(self.buffer_list) > 1:
                self.current_buffer = self.buffer_list[index]
            else:
                self.current_buffer = None
        self.buffer_list.remove(filepath)
        del self.buffers[filepath]
        self.master.bufferlist.update_buffers()
        return True

    def trigger_open(self, filepath, focus=True):
        if filepath in self.buffers:
            return self.trigger_focus(filepath)
        buffer = GtkSource.Buffer()
        fullpath = os.path.join(self.master.workdir, filepath)
        try:
            undo_manager = buffer.get_undo_manager()
            undo_manager.begin_not_undoable_action()
            with open(fullpath) as f:
                buffer.set_text(f.read())
            undo_manager.end_not_undoable_action()
        except Exception as e:
            print(f"Error opening file {fullpath}: {e}")
            return False
        start_iter = buffer.get_start_iter()
        buffer.place_cursor(start_iter)
        #detect language
        language = self.lang_manager.guess_language(os.path.basename(filepath), None)
        if language:
            buffer.set_language(language)
        buffer.set_style_scheme(self.scheme)
        buffer.filepath = filepath
        buffer.connect("changed", self.on_buffer_change)
        self.buffers[filepath] = {
            "buffer": buffer,
            "path": filepath,
            "language":  language,
            "spaces_to_tabs": True,
            "tab_width": 4,
            "mode": "saved"
        }
        self.buffer_list.append(filepath)
        return self.trigger_focus(filepath)

    def on_buffer_change(self, buffer):
        if self.buffers[buffer.filepath]["mode"] == "modified":
            return False
        self.buffers[buffer.filepath]["mode"] = "modified"
        self.provider.set_buffer(buffer.filepath, buffer)
        self.master.bufferlist.update_buffers()

