import inspect
import sys
from mockchain.crypto import hash

def env_to_string(env):
    res = ""
    for key, value in env.items():
        if res == "":
            res = "{"
        else:
            res = res + ", "

        if callable(value):
            res += f"{key}:<function>" 
        elif type(value) == int:
            res += f"{key}:{value}"
        elif type(value) == str:
            res += f"{key}:'{value}'"
        else:
            res += f"{key}:{value}"

    res += "}"
    return res

class Program:
    def __init__(self, functions):
        if not isinstance(functions, list):
            functions = [functions]

        self.sources = "\n".join([inspect.getsource(f) for f in functions])
        self.target_function = functions[-1].__name__
        self.step = {}


    def compile(self):
        env =  {}
        exec(self.sources, env)
        func = env[self.target_function]
        return func, env
            
    def run(self, *args, **kwargs):
        func, env = self.compile()
        return func(*args, **kwargs)

    
    def trace(self, *args, **kwargs):
        func, env = self.compile()
        trace = []

        def callback(frame, event, arg):
            nonlocal trace
            if event == "line":
                trace.append(f"#{frame.f_lineno} {env_to_string(frame.f_locals)}")

            return callback

        sys.settrace(callback)
        try:
            result = func(*args, **kwargs)
            trace.append(f"Return: {str(result)}")
        finally:
            sys.settrace(None)

        hash_trace = list(map(hash, trace))

        for i in range(len(hash_trace)-1):
            self.step[hash_trace[i]] = hash_trace[i+1]

        return hash_trace, trace

