# course-graph

A graph visualization of courses and their prerequisites, built on
top of the [pyvis](https://pyvis.readthedocs.io/en/latest/index.html)
visualization library.

TODO: webscrapers for math course pages and OSCAR

## Installation

To install dependencies, run 
```bash
pipenv install
npm install
```

## Pyvis Notes

Pyvis itself is just a thin layer over the
[vis.js](https://visjs.org/) library, specifically the
[network](https://visjs.github.io/vis-network/docs/network/) module. Pyvis
simply generates a `.html` file which your browser renders with JavaScript.
This means that the library is a bit contradictory in some aspects ---
the programmer can try to use Python as much as possible, or they could
just pass in a JSON options dictionary to vis-network directly. Ideally Python
code should interface with Python code, but certain options are just different,
for example `Network.barnes_hut` has different defaults than just specifying
```javascript
var options = {
    "physics": {
        "enabled": true,
        "barnesHut": {
            ...
        }
    }
}
```

In addition, the HTML file Pyvis generates
1. Uses Cloudflare's CDN to load vis and
2. Uses an old version of vis, currently the 4.16.1 version.

[vis](https://www.npmjs.com/package/vis) has been deprecated
in favor of using each module directly, in this case
[vis-network](https://www.npmjs.com/package/vis-network). This project patches
the HTML file by replacing the header with local imports instead of using
an external CDN, and uses the most recent version of vis-network.

## Usage

Course prerequisites will sometimes include "or"'s in addition to "and"'s, for
example CS 3451 - Computer Graphics has the following prerequisites:
```text
(Undergraduate Semester level MATH 2605 Minimum Grade of D or
 Undergraduate Semester level MATH 2401 Minimum Grade of D or
 Undergraduate Semester level MATH 2411 Minimum Grade of D or
 Undergraduate Semester level MATH 24X1 Minimum Grade of T or
 Undergraduate Semester level MATH 2551 Minimum Grade of D or
 Undergraduate Semester level MATH 2550 Minimum Grade of D or
 Undergraduate Semester level MATH 2561 Minimum Grade of D or
 Undergraduate Semester level MATH 2X51 Minimum Grade of T
)
and
((Undergraduate Semester level CS 2110 Minimum Grade of C or
  Undergraduate Semester level CS 2261 Minimum Grade of C
 ) 
 or
 (Undergraduate Semester level ECE 2020 Minimum Grade of C and
  Undergraduate Semester level ECE 2035 Minimum Grade of C
 )
)
and
(Undergraduate Semester level CS 1332 Minimum Grade of C and
 Undergraduate Semester level CS 2340 Minimum Grade of C
)
```

There's two ways we can interpret this: through the semantic meaning of
the "or" itself, and through the effect it has on our prerequisite graph.
Fundamentally, we can't have or's in our graph, because there's no easy way
to represent or's other than making "meta-nodes" which encapsulate multiple
classes. Meta nodes are (1.) hard to interpret and (2.) clutter the graph. So
we're going to remove them, and the reason they're there in the first place
tells us how. "or's" represent different course _options_ we have. The reason
why there's MATH 2605 or 2401 or ... or 2X51 is because each one is essentially
a multivariate calculus class. There are multiple multivariate calculus classes
because some are old, some are honors classes, some are transfer credit, and
so on. So really the prerequisites for this computer graphics class is a
multivariate calculus class, a machine language class, a data structures class,
and a software engineering class. The or's just represent different options.

So how do we simply an arbitrarily nested string of "or's" and "and's" (which
has to be parsed into a tree in the most general case) into a depth 1 sequence
of and's? The answer, albeit a bit ad-hoc, is to simply pick a choice for each
or. As in, we would pick the single multivariate calculus that we have already
taken or plan to take. And whenever we see this class in a string of "or's", we
replace the entire term with just the single class. Note that this generates
a _more_ restrictive condition than we started out with, since if we've taken
the class, it automatically short-circuits the or, but we could have taken
a different class that satisfies the condition that we don't realize in the
simplified condition. 

So for each possible or, we pick a single class that replaces it.
It's annoying that we have to do this by hand, but it's not too bad.


## Examples

```bash
python graph.py --data data/courses.json --prune input/prune.txt --options input/json/cs_undergrad.json --undergrad
python graph.py --data data/courses.json --prune input/prune.txt --options input/json/cs_undergrad_cat.json --undergrad --color
python graph.py --data data/courses.json --prune input/prune.txt --options input/json/cs_grad.json -k 15
python graph.py --data data/courses.json --prune input/prune.txt --options input/json/cs_grad_cat.json -k 15 --color
```

