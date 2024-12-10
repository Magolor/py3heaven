import io
import contextlib
from .file_utils import *
Import("IPython",globals())

class Sandbox:
    def __init__(self, codes=list(), reset=False):
        super().__init__()
        self.shell = None; self.codes = codes
        if reset: self.reset()

    def __enter__(self):
        self.reset(); return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()

    def reset(self):
        self.exit()
        self.shell = IPython.terminal.embed.InteractiveShellEmbed(quiet=True)
        for code in self.codes:
            response = self.shell.run_cell(code)
            if not response.success:
                return {'status':False, 'response':None, 'msg':response['msg']}
        return {'status':True, 'response':self.shell.user_ns['_'], 'msg':None}

    def execute(self, code, reset=False):
        try:
            if reset:
                response = self.reset()
                if not response['status']:
                    return {'status':False, 'response':None, 'msg':str(response.error_in_exec)}
            with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                response = self.shell.run_cell(code)
            if response.success:
                return {'status':True, 'response':self.shell.user_ns['_'], 'msg':None}
            else:
                return {'status':False, 'response':None, 'msg':str(response.error_in_exec)}
        except Exception as e:
            return {'status':False, 'response':None, 'msg':str(type(e))+' '+str(e)}
    
    def add(self, code, index=-1):
        self.codes.insert(index, code)
    
    def pop(self, index=-1):
        return self.codes.pop(index)
    
    def get(self, key="_"):
        return self.shell.user_ns[key] if self.shell else None
    
    def export(self, path):
        with open(AsFormat(path, "py"), "w") as f:
            for code in self.codes:
                f.write("# %%\n")
                f.write(code)
                f.write("\n\n")
            f.write("# %%\n")
    
    def exit(self):
        if self.shell:
            self.shell.run_cell("quit()")
        self.shell = None

def Str2Code(code, env=None):
    pass

# def get_globals():
#     with Sandbox(codes=[]) as env:
#         response = env.execute("globals()")
#     if response['status']:
#         return response['response']
#     else:
#         return {}

class API:
    def __init__(self, **kwargs):
        super().__init__()
        self.config = kwargs
        assert ('name' in self.config), "Name is required!"
        assert ('inputs' in self.config), "Inputs are required!"
        assert ('outputs' in self.config), "Outputs are required!"
        assert (len(self.config['outputs'])==1), "Currently only single output is supported!"
        
        if ('env' not in self.config):
            self.env = Sandbox(codes=["from seed import *"])
        else:
            self.env = Sandbox(codes=self.config['env'])
    
    @property
    def name(self):
        return self.config['name']
    
    @property
    def output(self):
        # Currently only single output is supported!
        return self.config['outputs'][0]['name']
    
    @property
    def doc(self):
        return self.config['doc'] if 'doc' in self.config else ""
    
    @property
    def args(self):
        # attr1, attr2, attr3, ...
        return ', '.join(i['name'] for i in self.config['inputs'])
    
    @property
    def asgs(self):
        # attr1=attr1, attr2=attr2, attr3=attr3, ...
        return ', '.join(i['name']+'='+i['name'] for i in self.config['inputs'])
    
    def inps(self, inputs=dict()):
        # attr1=..., attr2=..., attr3=..., ...
        return ', '.join(i['name']+'='+repr(inputs[i['name']]) for i in self.config['inputs'] if i['name'] in inputs)
    
    def kwargs_call(self):
        # name(**kwargs)
        return self.config['name'] + '(**kwargs)'
    
    def args_call(self, with_kwargs=False):
        # name(attr1, attr2, attr3, ..., **kwargs)
        return self.config['name'] + '(' + self.args + (', **kwargs)' if with_kwargs else ')')
    
    def asgs_call(self, with_kwargs=False):
        # name(attr1=attr1, attr2=attr2, attr3=attr3, ..., **kwargs)
        return self.config['name'] + '(' + self.asgs + (', **kwargs)' if with_kwargs else ')')
    
    def api_def(self, with_kwargs=False):
        # def name(attr1, attr2, attr3, ..., **kwargs):
        return "def "+self.args_call(with_kwargs=with_kwargs)+":\n"
    
    def api_call(self, inputs, with_kwargs=False):
        # name(attr1=..., attr2=..., attr3=..., ..., **kwargs)
        return self.config['name'] + '(' + self.inps(inputs) + (', **kwargs)' if with_kwargs else ')')
    
    def api_execute(self, code, inputs):
        self.env.add(code); result = self.env.execute(self.api_call(inputs), reset=True); self.env.pop(); return result
