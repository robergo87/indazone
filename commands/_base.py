import os
import argparse
import hashlib

from unixsocket import send_message

baseparser = parser = argparse.ArgumentParser(
    description=""
)
BASE_COMMANDS = {}

def register_command(command: str, argparser, callback):
    BASE_COMMANDS[command] = argparser, callback, True

def register_client_command(command: str, argparser, callback):
    BASE_COMMANDS[command] = argparser, callback, False

def execute_command(argv, client=False, master=None, component=None):
    if len(argv) < 1 or argv[0] not in BASE_COMMANDS:
        
        baseparser = parser = argparse.ArgumentParser(
            description="GTK/Python based simple IDE"
        )
        baseparser.add_argument(
            "action", type=str, choices=list(BASE_COMMANDS),
            help='Action to be taken, use "run" to start editor'
        )
        base_args, _ = baseparser.parse_known_args(argv)
        return False, "Error parsing parameters"
    parser, callback, server_mode = BASE_COMMANDS[argv[0]]
    args = parser.parse_args(argv)
    if server_mode or client:
        if component:
            return True, callback(args, master=master, component=component)
        else:
            return True, callback(args, master=master)
    else:
        response = send_message(args.sessionid, list(argv))
        return response

class CommandParser(argparse.ArgumentParser):
    def __init__(self, command, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.add_argument(
            "action", type=str,
            choices=[command],
            help='Action to be taken, use "run" to start editor'
        )
        self.add_argument(
            "--workdir",
            type=str,
            default=os.getcwd(),
            help="Working directory (default: current directory)"
        )
        self.add_argument(
            "--sessionid",
            type=str,
            default="",
            help="Working directory (default: current directory)"
        )
        
    def parse_args(self, argv=None):
        if argv is None:
            response = super().parse_args()
        else:
            response = super().parse_args(argv)
        if not response.sessionid:
            hash = hashlib.md5(response.workdir.encode()).hexdigest()
            response.sessionid = f"rgide_{hash}"
        return response



