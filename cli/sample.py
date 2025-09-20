from ._base import register_command, ListSelector


@register_command("sample")
def sample(argv):
    items = ["Apple", "Banana", "Cherry", "Date"] * 10
    selector = ListSelector(items, multi=True)
    selected = selector.run()
    print(selected)

