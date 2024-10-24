# import ast
# import textwrap
# from collections import deque
# from typing import Deque
#
# from scalpel import cfg, import_graph
#
# src = textwrap.dedent(
#     """
# def f():
#     x = 1
#     try:
#         a = open("a.txt", "r")
#         x = 2
#         a.close()
#     except IOError:
#         x = 3
#     except:
#         x = 4
#     else:
#         x = 5
#     finally:
#         y = 1
#
#     y += 6
#     return x + y
# """
# )
#
#
# def foo():
#     c = cfg.CFGBuilder().build_from_src(name="top_level", src=src)
#     assert c is not None
#     for (_, _), fun_cfg in c.functioncfgs.items():
#         print("")
#
#
# def stuff():
#     p = ast.parse(src)
#     print(f"p.body {p.body}")
#     ast_f = ast.parse(src).body[0]
#     print(f"attributes {ast_f._attributes}")
#
#     # ast_f.
#     queue: Deque[ast.AST] = deque()
#     queue.append(ast_f)
#
#     while len(queue) > 0:
#         node = queue.popleft()
#
#         children = ast.iter_child_nodes(node)
#         for child in children:
#             queue.append(child)
#             print(f"{node.__str__}->{child.__str__}")
#
#
# if __name__ == "__main__":
#     foo()
