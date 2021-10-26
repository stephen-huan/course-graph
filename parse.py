from typing import Union


class Term:

    """ Represents a logical term. """

    def __init__(self, op: str, children: list) -> None:
        assert op in {"and", "or"}, f"operator {op} is not valid"
        assert len(children) > 0, "cannot have no children"

        self.op = op
        self.children = children

    def __str__(self) -> str:
        """ Displays the expression in-line with infix notation. """
        return "(" + (f" {self.op} ").join(map(str, self)) + ")"

    def __len__(self) -> int:
        """ Implements the sequence protocol with __getitem__. """
        return len(self.children)

    def __getitem__(self, key: int) -> Union["Term", str]:
        """ Implements the sequence protocol with __len__. """
        return self.children[key]

    def binary(self) -> "Term":
        """ Returns an equivalent binary tree. """
        binary = lambda node: node.binary() if isinstance(node, Term) else node
        tree = binary(self[0])
        for child in self[1:]:
            tree = Term(self.op, [tree, binary(child)])
        return tree

    def collapse(self) -> "Term":
        """ Returns an equivalent condensed tree. """
        children = []
        for child in self:
            child = child.collapse() if isinstance(child, Term) else child
            # if child has same operation as parent, add child's children
            children += child if isinstance(child, Term) \
                and child.op == self.op else [child]
        return Term(self.op, children)


def match(s: str, i: int, patterns: list) -> int:
    """ Matches every pattern against the current position in s,
        returning an index if found and None if not found. """
    for k, pattern in enumerate(patterns):
        if s[i: i + len(pattern)] == pattern:
            return k

def parse_tokens(op: str, tokens: list) -> Union[Term, str]:
    """ Parses a list of tokens into a Term object. """
    tokens = [parse_tree(token[1:-1]) if isinstance(token, str) and \
              token[0] == "(" and token[-1] == ")" else token
              for token in tokens]
    return tokens[0] if len(tokens) == 1 else Term(op, tokens)

def parse_tree(s: str) -> Union[Term, str]:
    """ Recursively build a parse tree on the string. """
    # force parser to add last token, avoiding the edge case
    ops = [" or ", " and "]
    s += ops[0]
    tokens, stk, i, depth = [], [], 0, 0

    while i < len(s):
        # only process top-level tokens, i.e. skipping if we're in (...)
        index = match(s, i, ops)
        if depth == 0 and index is not None:
            # remove extraneous whitespace
            tokens.append("".join(stk).strip())
            tokens.append(ops[index].strip())
            stk = []
            i += len(ops[index])
        else:
            stk.append(s[i])
            # entered or leaving a token
            if s[i] in "()":
                depth += 1 if s[i] == "(" else -1
            i += 1

    terms, stk, i = [], [], 0
    while i < len(tokens):
        if i % 2 == 1: # operator
            # accumulate and, break on or
            if tokens[i] == "or":
                terms.append(parse_tokens("and", stk))
                stk = []
        else:          # tree
            stk.append(tokens[i])
        i += 1

    return parse_tokens("or", terms)

def parse(s: str) -> Term:
    """ Thin wrapper over parse_tree. """
    tree = parse_tree(s)
    tree = tree if isinstance(tree, Term) else Term("and", [tree])
    return tree.collapse()

if __name__ == "__main__":
    s = "a and b and c or (a and b and (a or c) and b) or (c and d ) and e"
    tree = parse(s)

    print(tree)
    print(tree.binary())
    print(tree.binary().collapse())
    for term in tree:
        print(term)

