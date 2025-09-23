import subprocess

from ._base import register_command, ListSelector


@register_command("gitadd")
def sample(argv):
    result = subprocess.run(
        ["git", "status", "-s"],    # command as list
        capture_output=True,
        text=True                   # decode to string instead of bytes
    )
    if result.returncode:
        print(result.stderr)
        return
    items = [row.strip() for row in result.stdout.split("\n") if row.strip()]
    if not items:
        print("Up to date")
    
    selector = ListSelector(items, multi=True)
    selected = [row[2:].strip() for row in selector.run()]
    if not selected:
        print("No files to add")
        return
    result = subprocess.run(
        ["git", "add"] + selected,    # command as list
        capture_output=True,
        text=True                   # decode to string instead of bytes
    )
    if result.returncode:
        print(result.stderr)
        return
    print(result.stdout)
