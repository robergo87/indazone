import sys
import curses

BASE_COMMANDS = {}

def register_command(command: str):
    def inner(callback):
        BASE_COMMANDS[command] = callback
        return callback
    return inner

def exec_cli():
    if len(sys.argv) < 2:
        return
    if sys.argv[1] not in BASE_COMMANDS:
        return
    BASE_COMMANDS[sys.argv[1]](sys.argv[2:])
    sys.exit()


class ListSelector:
    def __init__(self, options, multi=False, formatter=None, callback=None):
        self.options = options
        self.multi = multi
        self.callback = callback
        if not formatter:
            def formatter(content):
                return str(content)
        self.formatter = formatter
        if multi:
            self.selected = [0] * len(options)
        else:
            self.selected = -1
        self.current = 0
        self.window_start = 0
        self.stdscr = None

    def draw(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx() 
        for index in range(self.window_start, min(self.window_start+h-1, len(self.options))):
            option = self.options[index]
            selected = self.selected[index] if self.multi else self.selected == index
            icon = "+" if selected else " "
            line = self.formatter(option)[0:w-5].ljust(w-5, " ")
            if index == self.current:
                self.stdscr.addstr(f"[{icon}] {line}\n", curses.A_REVERSE)
            else:
                self.stdscr.addstr(f"[{icon}] {line}\n")

    def move(self, offset):
        h, w = self.stdscr.getmaxyx() 
        self.current = min( max(0, self.current+offset), len(self.options)-1)
        if self.current < self.window_start:
            self.window_start = self.current
        if self.current > self.window_start + h - 2:
            self.window_start = self.current - h + 2

    def select_item(self):
        if self.multi:
            self.selected[self.current] = int( not bool(self.selected[self.current]) )
        else:
            self.selected = self.current

    def run(self):
        def inner(stdscr):
            self.stdscr = stdscr
            self.stdscr.clear()
            curses.curs_set(0)  # hide cursor

            while True:
                self.draw()
                keypressed = self.stdscr.getch()
                if keypressed in [curses.KEY_UP, ord('k')]:
                    self.move(-1)
                elif keypressed in [curses.KEY_DOWN, ord('j')]:
                    self.move(1)
                elif keypressed in [32, ord(' ')]:
                    self.select_item()
                elif keypressed in [23, ord('\t')]:
                    self.select_item()
                    self.move(1)                
                elif keypressed in [curses.KEY_ENTER, 10, 13]:
                    if not self.multi:
                        self.select_item()
                    if self.callback:
                        if self.multi:
                            self.callback([
                                self.options[index] for index, val in enumerate(self.selected) 
                            ])
                            continue
                        else:
                            if self.callback(self.options[self.selected]):
                                break
                    else:
                        break
                elif keypressed in [27]:
                    if self.multi:
                        self.selected = []
                    else:
                        self.selected = -1
                    break
                else:
                    return "    "+str(keypressed)
            if self.multi:
                return [self.options[i] for i, val in enumerate(self.selected) if val]
            else:
                return self.options[self.selected] if self.selected != -1 else None
            print(self.selected)
        return curses.wrapper(inner)





