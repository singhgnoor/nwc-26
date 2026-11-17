"""The college machine may run an old Python: keep every script parseable and runnable on 3.8.

This cannot replace running the tests on a real 3.8, but it catches the usual mistakes:
3.9+ syntax, `list[str]`-style hints, `X | Y` unions, and 3.9+ library calls.
"""
import ast
import os
import unittest

from tests.helpers import REPO

FILES = ["server.py", "build_site.py"] + [os.path.join("tests", f) for f in sorted(os.listdir(os.path.join(REPO, "tests")))
                                          if f.endswith(".py")]
NEWER_THAN_38 = ("removeprefix", "removesuffix", "zoneinfo", "is_relative_to", "randbytes", "cache_clear",
                 "functools.cache", "graphlib", "tomllib", "ExceptionGroup", "TaskGroup", "batched")
BUILTIN_GENERICS = {"list", "dict", "tuple", "set", "frozenset", "type"}


class TestPython38Compatibility(unittest.TestCase):
    def test_parses_with_python38_grammar(self):
        for name in FILES:
            with self.subTest(file=name):
                with open(os.path.join(REPO, name), encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=name, feature_version=(3, 8))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                        self.assertNotIn(node.value.id, BUILTIN_GENERICS,
                                         "%s:%d uses %s[...] (3.9+)" % (name, node.lineno, node.value.id))
                    if isinstance(node, ast.Match if hasattr(ast, "Match") else ()):
                        self.fail("%s:%d uses match (3.10+)" % (name, node.lineno))
                    for annotation in _annotations(node):
                        for sub in ast.walk(annotation):
                            if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr):
                                self.fail("%s:%d uses X | Y in a type hint (3.10+)" % (name, node.lineno))
                for word in NEWER_THAN_38:
                    self.assertNotIn(word, source.replace("NEWER_THAN_38", ""), "%s uses %s (3.9+)" % (name, word)) \
                        if name != os.path.join("tests", "test_py38_compat.py") else None


def _annotations(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = node.args
        for a in args.args + args.kwonlyargs + getattr(args, "posonlyargs", []):
            if a.annotation is not None:
                yield a.annotation
        if node.returns is not None:
            yield node.returns
    elif isinstance(node, ast.AnnAssign):
        yield node.annotation


if __name__ == "__main__":
    unittest.main()
