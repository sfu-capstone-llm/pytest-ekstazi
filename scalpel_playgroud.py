import ast
import textwrap

from scalpel import cfg, import_graph


def foo():
    src = textwrap.dedent(
        """
    def f():
        x = 1
        try:
            a = open("a.txt", "r")
            x = 2
            a.close()
        except IOError:
            x = 3
        except:
            x = 4
        else:
            x = 5
        finally:
            y = 1
        
        y += 6
        return x + y    
    """
    )

    p = ast.parse(src)
    print(p.body)
    ast_f = ast.parse(src).body[0]
    print(ast_f._attributes)


if __name__ == "__main__":
    foo()
