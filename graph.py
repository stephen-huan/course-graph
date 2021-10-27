import argparse, os, json
import course as cs
import far

# default course category
DEFAULT = "Miscellaneous"
# taken from https://www.cc.gatech.edu/threads-better-way-learn-computing
COLOR_LIST = [
    (  2, 112, 112), # devices
    (193, 215,  61), # info
    (  4, 173, 238), # intelligence
    (246, 146,  30), # media
    (240, 240, 240), # misc.
    (101,  45, 145), # mod & sim
    ( 37, 143,  59), # people
    (236,   2, 140), # sys & arch
    (  0,  84, 166), # theory
]

def rgb_hsv(rgb: tuple) -> tuple:
    """
    Converts a RGB color to a HSV.
    See: https://en.wikipedia.org/wiki/HSL_and_HSV#From_RGB
    """
    rgb = tuple(x/255 for x in rgb)
    i = max(range(3), key=lambda i: rgb[i])
    V, C = rgb[i], rgb[i] - min(rgb)
    S = C/V if V > 0 else 0
    H = 60*(2*i + (rgb[(i + 1) % 3] - rgb[(i + 2) % 3])/C) if C > 0 else 0
    return (H % 360, S, V)

def hsv_rgb(hsv: tuple) -> tuple:
    """
    Converts a HSV color to RGB.
    See: https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB
    """
    H, S, V = hsv
    f = lambda n: \
        (lambda n, k: V - V*S*max(0, min((k, 4 - k, 1))))(n, (n + H/60) % 6)
    return tuple(round(255*x) for x in (f(5), f(3), f(1)))

# HSV: (original hue, low saturation, high value)
pastel = lambda color: hsv_rgb((rgb_hsv(color)[0], 0.2, 1))
COLOR_LIST = ["rgba({}, {}, {}, 0.8)".format(*pastel(color))
              for color in COLOR_LIST]
COLOR_LIST[4] = "rgba(240, 240, 240, 0.8)"

### graph functions

def dfs(graph: dict, start: str) -> dict:
    """ Depth-first-search to find the distance between nodes. """
    seen = {start: 0}
    stk = [start]
    while len(stk) > 0:
        node = stk.pop()
        for child in graph[node]:
            if child not in seen:
                seen[child] = seen[node] + 1
                stk.append(child)
    return seen

def assign(graph: dict, start: str, index: int, ids: dict) -> None:
    """ Assigns every reachable node from start to the component index. """
    stk = [start]
    ids[start] = index
    while len(stk) > 0:
        node = stk.pop()
        for child in graph[node]:
            if child not in ids:
                ids[child] = index
                stk.append(child)

def connected(graph: dict) -> tuple:
    """ Finds the connected components of an undirected graph. """
    ids, index = {}, 0
    for node in graph:
        if node not in ids:
            assign(graph, node, index, ids)
            index += 1
    return ids, index

### helper methods

def is_simple(tree: cs.Term) -> bool:
    """ Whether the tree is depth 1 with and conditions. """
    return tree is None or (tree.op == "and" and \
        all(isinstance(child, cs.Course) for child in tree))

def color(course: str) -> str:
    """ Gets the color of a course. """
    # default color
    color = "rgba(240, 240, 240, 0.8)"
    if len(taken) == 0:
        return color
    # taken course
    if course in taken:
        color = "rgba(220, 220, 256, 0.8)"
    # able to take course
    elif trees[course] is None or trees[course].valid(taken):
        color = "rgba(220, 256, 220, 0.8)"
    return color

def category(course: str) -> str:
    """ Returns the color category of a course. """
    return palette[course_data[course].get("category", DEFAULT)]

def header(course: str) -> str:
    """ Returns a header summary for the course. """
    title = course_data.get(course, {}).get("title", "???")
    return f"{str(course):9} - {title:25}"

def description(course: str) -> str:
    """ Returns a long description of the course. """
    data = course_data[course]
    body = far.process(data["description"].split(), 40, "")
    prereqs = None if trees[course] is None else \
        " and ".join(course if course in taken else f"*{course}*"
                     for course in str(trees[course])[1:-1].split(" and "))
    return \
f"""
*{course} - {data['title']}*
{body}

{data['credit']} credit hours

*Prerequisites:*
{prereqs}
""".strip()

def patch(fname: str) -> None:
    """ Replace the header of the generated html file to use local imports. """
    header = \
"""
<html>
<head>
<!-- <link rel="stylesheet" href="../node_modules/vis/dist/vis.css" type="text/css" />
<script type="text/javascript" src="../node_modules/vis/dist/vis-network.min.js"> </script>-->
<center>
<h1></h1>
</center>

<!-- use the new version of vis-network -->
<link rel="stylesheet" href="../node_modules/vis-network/dist/dist/vis-network.css" type="text/css" />
<script type="text/javascript" src="../node_modules/vis-network/dist/vis-network.min.js"> </script>
""".strip()

    with open(fname) as f:
        lines = f.readlines()

    with open(fname, "w") as f:
        for line in [line + "\n" for line in header.splitlines()] + lines[10:]:
            f.write(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Course prerequisite graph")
    parser.add_argument("-v", "--version", action="version", version="1.0")
    parser.add_argument("-d", "--data", required=True,
                        help="course data JSON file")
    parser.add_argument("-c", "--course", help="course list text file")
    parser.add_argument("-p", "--prune", help="prune courses text file")
    parser.add_argument("-t", "--taken", help="taken courses text file")
    parser.add_argument("-k", "--components", type=int, default=1,
                        help="number of connected components to display")
    parser.add_argument("-u", "--undergrad", action="store_true",
                        help="only show undergraduate courses")
    parser.add_argument("-C", "--color", action="store_true",
                        help="color code based on cateogry")
    parser.add_argument("-s", "--seed", type=int, help="random seed")
    parser.add_argument("-o", "--options", help="options JSON file")

    args = parser.parse_args()

    with open(args.data) as f:
        course_data = json.load(f)

    # map category name to color
    if args.color:
        categories = sorted(set(data.get("category", DEFAULT)
                                for data in course_data.values()))
        palette = dict(zip(categories, COLOR_LIST))

    # load course list, prune list, and taken classes
    courses = sorted(course_data.keys()) if args.course is None else \
        cs.load_file(args.course)
    course_prune = set(cs.load_file(args.prune))
    taken = set(cs.load_file(args.taken))

    # generate prerequisite trees for each course
    trees = {}
    for cid in sorted(courses):
        trees[cid] = cs.parse_prereq(course_data[cid]["prereqs"], course_prune)
        # print(f"{header(cid)} {trees[cid]}")

    assert all(map(is_simple, trees.values())), "trees are not simple"

    ### generating and visualizing graph

    from pyvis.network import Network

    # node A points to node B if B has A as a prerequisite 
    graph = {course: [] for course in courses}
    undirected = {course: [] for course in courses}
    for course in sorted(courses):
        # skip graduate courses
        tokens = course.split()
        department, cid = tokens[0], " ".join(tokens[1])
        if args.undergrad and not cs.Course(department, cid).undergrad:
            continue
        for child in (trees[course] if trees[course] is not None else []):
            if child in courses:
                graph[child].append(course)
                undirected[child].append(course)
                undirected[course].append(child)

    # generate connected components of underlying undirected graph
    ids, index = connected(undirected)
    comps = {i: [] for i in range(index)}
    for key, value in ids.items():
        comps[value].append(key)
    # take only the k largest components
    order = sorted(comps,
                   key=lambda i: len(comps[i]), reverse=True)[:args.components]
    courses = [str(course) for i in order for course in comps[i]]
    render = set(courses)

    # make pyvis network
    net = Network(directed=True, width="2560px", height="1440px")

    for course in courses:
        colors = {"background": color(course)}
        if args.color:
            colors["border"] = category(course)
            colors["background"] = category(course)
        net.add_node(course,
                     title=description(course),
                     label=course_data[course]["title"],
                     shape="box",
                     color=colors,
                     # borderWidth=2,
                    )

    for node in graph:
        for child in graph[node]:
            if node in render and child in render:
                net.add_edge(node, child)

    # create legend
    # not sure how to do this without affecting the resulting graph
    if args.color:
        for i, category in enumerate(categories):
            net.add_node(category,
                         title=category,
                         label=category,
                         shape="box",
                         color=palette[category],
                         physics=False,
                         x=1000,
                         y=-1000 + 32*i,
                        )

    options = """
var options = {
    "configure": {
        "enabled": false
    },
    "interaction": {
        "keyboard": true
    },
    "layout": {
        "randomSeed": 1
    },
    "edges": {
        "color": {
            "inherit": "to"
        }
    },
    "physics": {
        "enabled": true,
        "barnesHut": {
            "gravitationalConstant": -4000
        },
        "stabilization": {
            "enabled": true,
            "fit": true,
            "iterations": 1000,
            "onlyDynamicEdges": false,
            "updateInterval": 50
        }
    }
}
""" if args.options is None else open(args.options).read()
    net.set_options(options)
    out = "output/graph.html"
    if not os.path.exists("output"):
        os.mkdir("output")
    net.show(out)
    patch(out)

    ### counting prerequisites

    count = {}
    for tree in trees.values():
        for child in (tree if tree is not None else []):
            count[child] = count.get(child, 0) + 1

    # for course in sorted(count, key=count.get, reverse=True)[:20]:
    #     print(f"{header(course)} {count[course]}")

    ### deepest path in graph

    deepest, length = None, -1
    for course in graph:
        dist = dfs(graph, course)
        depth = max(dist.values())
        if depth > length:
            deepest, length = course, depth

    # print(f"{deepest} ->")
    # for course, dist in sorted(dfs(graph, deepest).items(),
    #                            key=lambda x: x[1]):
    #     print(f"-> {header(course)}, {dist}")

