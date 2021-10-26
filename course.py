import argparse
from typing import Union
import parse


class Course:

    """ Represents a course at Georgia Tech. """

    def __init__(self, department: str, cid: str) -> None:
        self.department, self.cid = department, cid
        self.undergrad = int(cid[0]) < 5

    def __eq__(self, other: "Course") -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return f"{self.department} {self.cid}"


class Term(parse.Term):

    """ Process Term objects by changing leaves to Course objects. """

    def __init__(self, course_prune: list, term: parse.Term) -> None:
        self.course_prune = course_prune
        self.op = term.op

        def process(child: Union[parse.Term, Course, str]) \
                -> Union[Term, Course]:
            """ Processes the given child. """
            if isinstance(child, parse.Term):
                return Term(course_prune, child).prune()
            elif isinstance(child, str):
                return to_course(child)
            else:
                return child

        self.children = list(map(process, term))

    def prune(self) -> "Term":
        """ Removes equivalent courses. """
        pruneable = [child for child in self if child in self.course_prune]
        return pruneable[0] if self.op == "or" and len(pruneable) > 0 else self

    def valid(self, courses: list) -> bool:
        """ Whether the given taken courses satisfies the prerequisites. """
        return (any if self.op == "or" else all)(
            child.valid(courses) if isinstance(child, Term) else \
            child in courses for child in self)


def load_file(fname: Union[str, None]) -> list:
    """ Reads a text file. """
    if fname is None:
        return []
    with open(fname) as f:
        process = lambda line: line.split("#")[0].strip()
        return [line for line in map(process, f.readlines()) if line]

def to_course(raw: str) -> Course:
    """ Converts raw course registration data into Course objects. """
    return Course(*raw.split()[3:5])

def prune(tree: Term) -> Term:
    """ Prunes the given tree by union'ing classes in an or. """
    course_prune, tree = tree.course_prune, tree.prune()
    return tree if isinstance(tree, Term) else \
        Term(course_prune, parse.Term("and", [tree]))

def parse_prereq(s: str, course_prune: list) -> Term:
    """ Parses the prerequisite string into a Term tree. """
    return prune(Term(course_prune, parse.parse(s))) if len(s) != 0 else None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Course prerequisite parser")
    parser.add_argument("-v", "--version", action="version", version="1.0")
    parser.add_argument("string", help="prerequisite string from OSCAR")
    parser.add_argument("-p", "--prune", help="prune courses text file")
    parser.add_argument("-t", "--taken", help="taken courses text file")

    args = parser.parse_args()

    course_prune = set(load_file(args.prune))
    courses = set(load_file(args.taken))
    tree = parse_prereq(args.string, course_prune)

    print(tree)
    print(f"You can{'' if tree.valid(courses) else 'not'} take the class")

