from src.lexer import Lexer
from src.parser import Parser, Program, Assignment, Expression, Term, Factor

def print_ast(node, level=0):
    indent = '  ' * level
    print(f'{indent}{type(node).__name__}')
    if isinstance(node, Program):
        for statement in node.statements:
            print_ast(statement, level + 1)
    elif isinstance(node, Assignment):
        print(f'{indent}  Identifier: {node.identifier}')
        print_ast(node.expression, level + 1)
    elif isinstance(node, Expression) or isinstance(node, Term):
        print_ast(node.left, level + 1)
        print(f'{indent}  Operator: {node.operator}')
        print_ast(node.right, level + 1)
    elif isinstance(node, Factor):
        print(f'{indent}  Value: {node.value}')

def main():
    source_code = "x = 5 + 3 * (2 - 8)"
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print_ast(ast)

if __name__ == "__main__":
    main()
