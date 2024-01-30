from pygame_monitor import *
def find_all_children(self, element: Widget):
    found_children = []



def find_all_children(root: Widget) -> list[Widget]:
        visited = set()  # Set to keep track of visited nodes
        unique_children = []  # List to store unique children

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for child in node.elements:
                unique_children.append(child)
                dfs(child)

        dfs(root)
        return unique_children

def get_children_needs_updating(root) -> list[Widget]:
    needs_updating = []
    children = find_all_children(root)
    for child in children:
        if child.needs_updating:
            needs_updating.append(child)
    return needs_updating