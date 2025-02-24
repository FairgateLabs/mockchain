import inspect
import textwrap
import sys
from mockchain.crypto import hash, Address, Cryptic
import mockchain.cardano

import code
import types
import os

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
    cache = {}

    @staticmethod
    def address(*functions, **globals):
        sources = "\n".join([inspect.getsource(f) for f in functions])
        target_function = functions[0].__name__
        
        codehash = hash(sources + "\n" + str(globals))

        if not codehash in Address.cache:
            Cryptic.add(target_function, codehash)
            globals = globals.copy()
            globals["Value"]=mockchain.cardano.Value
            globals["ScriptPurpose"]=mockchain.cardano.ScriptPurpose
            globals["ScriptContext"]=mockchain.cardano.ScriptContext

            p = Program(sources, target_function, codehash, globals)
            address = Address(p, codehash, True)
            Address.cache[codehash] = address

        return Address.cache[codehash]
    
    @staticmethod
    def get(codehash : str):
        if codehash in Address.cache:
            return Address.cache[codehash].program
        
        return None
    
    @staticmethod
    def call(codehash : str, *args, **kwargs):
        p = Program.get(codehash)
        if p is None:
            raise Exception(f"Program not found")
            
        return p.run(*args, **kwargs)
    

    def __init__(self, source, target_function, codehash, globals):
        self.sources = textwrap.dedent(source)
        self.target_function = target_function
        self.globals = globals
        self.codehash = codehash
        self.cnt = 0
        self.step = {}
        self.compiled_code = None
        self.compiled_code = self.compile()

    def compile(self):
        if self.compiled_code is not None:
            return self.compiled_code

        if not os.path.exists(".programs"):
            os.makedirs(".programs")

        filename=".programs/"+self.codehash+".py"
        with open(filename, "w") as f:
            f.write(self.sources)

        compiled_code = code.compile_command(self.sources, filename, "exec")
        env = self.globals.copy()
        exec(compiled_code, env)

        return compiled_code
    
            
    def build(self):
        env = self.globals.copy()
        exec(self.compiled_code, env)
        func = env[self.target_function]
        func = types.FunctionType(func.__code__, env, func.__name__)

        return func, env
    
    def run(self, *args, **kwargs):
        func, env = self.build()
        self.cnt += 1
        return func(*args, **kwargs)

    def trace(self, *args, **kwargs):
        func, env = self.build()
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

