import os
from enum import IntEnum
from collections import namedtuple
from struct import unpack_from, calcsize
from select import poll
from time import sleep
from ctypes import CDLL, get_errno, c_int
from ctypes.util import find_library
from errno import EINTR
from termios import FIONREAD
from fcntl import ioctl
from io import FileIO
from os import fsencode, fsdecode


__version__ = '2.0.1 '

__all__ = ['Event', 'INotify', 'flags', 'masks', 'parse_events']

_libc = None


def _libc_call(function, *args):
    """Wrapper which raises errors and retries on EINTR."""
    while True:
        rc = function(*args)
        if rc != -1:
            return rc
        errno = get_errno()
        if errno != EINTR:
            raise OSError(errno, os.strerror(errno))


Event = namedtuple('Event', ['wd', 'mask', 'cookie', 'name'])

_EVENT_FMT = 'iIII'
_EVENT_SIZE = calcsize(_EVENT_FMT)


class INotify(FileIO):
    fd = property(FileIO.fileno)

    def __init__(self, inheritable=False, nonblocking=False, closefd=True):            
        global _libc; _libc = _libc or CDLL(find_library('c'), use_errno=True)
        flags = (not inheritable) * os.O_CLOEXEC | bool(nonblocking) * os.O_NONBLOCK
        fd = _libc_call(_libc.inotify_init1, flags)
        super().__init__(fd, mode='rb', closefd=closefd)
        self._poller = poll()
        self._poller.register(self.fileno())

    def add_watch(self, path, mask):
        return _libc_call(_libc.inotify_add_watch, self.fileno(), fsencode(path), mask)

    def rm_watch(self, wd):
        _libc_call(_libc.inotify_rm_watch, self.fileno(), wd)

    def read(self, timeout=None, read_delay=None):
        data = self._readall()
        if not data and timeout != 0 and self._poller.poll(timeout):
            if read_delay is not None:
                sleep(read_delay / 1000.0)
            data = self._readall()
        return parse_events(data)

    def _readall(self):
        bytes_avail = c_int()
        ioctl(self, FIONREAD, bytes_avail)
        if not bytes_avail.value:
            return b''
        return os.read(self.fileno(), bytes_avail.value)


def parse_events(data):
    pos = 0
    events = []
    while pos < len(data):
        wd, mask, cookie, namesize = unpack_from(_EVENT_FMT, data, pos)
        pos += _EVENT_SIZE + namesize
        name = data[pos - namesize : pos].split(b'\x00', 1)[0]
        events.append(Event(wd, mask, cookie, fsdecode(name)))
    return events


class flags(IntEnum):
    ACCESS = 0x00000001  #: File was accessed
    MODIFY = 0x00000002  #: File was modified
    ATTRIB = 0x00000004  #: Metadata changed
    CLOSE_WRITE = 0x00000008  #: Writable file was closed
    CLOSE_NOWRITE = 0x00000010  #: Unwritable file closed
    OPEN = 0x00000020  #: File was opened
    MOVED_FROM = 0x00000040  #: File was moved from X
    MOVED_TO = 0x00000080  #: File was moved to Y
    CREATE = 0x00000100  #: Subfile was created
    DELETE = 0x00000200  #: Subfile was deleted
    DELETE_SELF = 0x00000400  #: Self was deleted
    MOVE_SELF = 0x00000800  #: Self was moved

    UNMOUNT = 0x00002000  #: Backing fs was unmounted
    Q_OVERFLOW = 0x00004000  #: Event queue overflowed
    IGNORED = 0x00008000  #: File was ignored

    ONLYDIR = 0x01000000  #: only watch the path if it is a directory
    DONT_FOLLOW = 0x02000000  #: don't follow a sym link
    EXCL_UNLINK = 0x04000000  #: exclude events on unlinked objects
    MASK_ADD = 0x20000000  #: add to the mask of an already existing watch
    ISDIR = 0x40000000  #: event occurred against dir
    ONESHOT = 0x80000000  #: only send event once

    @classmethod
    def from_mask(cls, mask):
        return [flag for flag in cls.__members__.values() if flag & mask]


class masks(IntEnum):
    CLOSE = flags.CLOSE_WRITE | flags.CLOSE_NOWRITE
    MOVE = flags.MOVED_FROM | flags.MOVED_TO
    ALL_EVENTS  = (flags.ACCESS | flags.MODIFY | flags.ATTRIB | flags.CLOSE_WRITE |
        flags.CLOSE_NOWRITE | flags.OPEN | flags.MOVED_FROM | flags.MOVED_TO | 
        flags.CREATE | flags.DELETE| flags.DELETE_SELF | flags.MOVE_SELF)
