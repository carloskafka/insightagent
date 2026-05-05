import ast

def safe_eval(expr: str):
    try:
        tree = ast.parse(expr, mode="eval")
        return str(eval(expr))
    except:
        return "error"