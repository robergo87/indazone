import subprocess
import argparse
import os

from ._base import register_command, ListSelector

parser = parser = argparse.ArgumentParser(
    description="Pattern to look for"
)
parser.add_argument(
    "pattern", type=str,
    help="Pattern to look for"
)
parser.add_argument(
    "--ext", type=str, default="",
    help="File extensions, comma separated"
)

def formatter(row):
    return f"{row['path']} {row['lineno']}:{row['line']}"

def callback(row):
    command = ["idz", "open", row["path"]]
    subprocess.run(command)
    command = ["idz", "editor-go-to-line", str(row["lineno"])]
    subprocess.run(command)   
    return False

def workdir():
    command = ["idz", "workdir"]
    result = subprocess.run(command, capture_output=True, text=True)    
    return result.stdout

def go_to_row(row):
    command = ["idz", "open", row["path"]]
    subprocess.run(command)
    command = ["idz", "editor-go-to-line", row["lineno"]]
    subprocess.run(command)
        
    return result.stdout
    

@register_command("find")
def sample(argv):
    args = parser.parse_args(argv)
    command = ["grep", "-rn"]
    if args.ext:
        ext_list = ",".join(["*."+ext.strip() for ext in args.ext.split(",")])
        command += [f'--include="{ext_list}"']
    command += [args.pattern, "."]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(result.stderr)
        return
    rows = []
    wd = workdir()
    for line in result.stdout.split("\n"):
        if not line.strip():
            continue
        line_split = line.split(":")
        row = {
            "rel": line_split[0], 
            "lineno": int(line_split[1]),
            "line": ":".join(line_split[2:])
        }
        row["abs"] = os.path.abspath(row["rel"])
        row["path"] = row["abs"][len(wd):]
        rows.append(row)
    if not rows:
        print("No results found")

    ListSelector(rows, formatter=formatter, callback=callback).run()
