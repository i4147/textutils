import abc
import os
from .fileref import FileRef, FileUse


class Extra:
    def __init__(self, name, files, subtype, options):
        self.name = name
        self.files = files
        self.subtype = subtype
        self.options = options


class Step(metaclass=abc.ABCMeta):
    name = ""

    def __init__(self, files, subtype, options, extras):
        self.extras = extras
        if not all(self.handles_extra_type(x.name) for x in extras):
            msg = "Invalid extra type: {} for {}".format(", ".join(x.name for x in extras), self.name)
            raise ValueError(msg)
        self.options = options
        self.subtype = subtype
        self.files = files
        if files:
            self.input = files[0]
        else:
            self.input = None
        self.output = None
        self.next = None
        self.prev = None

    def handles_extra_type(self, et: str):
        return False

    def set_input(self, fr):
        self.input = fr

    def set_output(self, fr):
        self.output = fr

    @abc.abstractmethod
    def solve_inout(self):
        pass

    def set_next(self, nx):
        self.next = nx

    def set_prev(self, pv):
        self.prev = pv

    @abc.abstractmethod
    def get_input_types_valid(self):
        return []

    @abc.abstractmethod
    def get_output_type(self):
        return ""

    @abc.abstractmethod
    def get_products(self):
        return [self.output]

    @abc.abstractmethod
    def get_dependencies_for(self, product):
        if product == self.output:
            return self.files
        return []

    @abc.abstractmethod
    def get_command_for(self, product):
        return ["echo", "not implemented"]


class Sink(Step):
    def __init__(self, files, subtype, options, extras):
        super().__init__(files, subtype, options, extras)
        if not self.files:
            msg = "Missing output file for sink {}".format(self.name)
            raise ValueError(msg)
        self.output = self.input
        self.input = None

    def get_input_types_valid(self):
        return [self.name]

    def get_products(self):
        return []

    def get_dependencies_for(self, product):
        return []

    def get_command_for(self, product):
        return []

    def get_output_type(self):
        return self.name

    def solve_inout(self):
        pass


class Pipeline:
    def __init__(self, steps, root=""):
        self.steps = steps
        self.root = root
        self.all_inputs = set()
        for j, i in enumerate(steps):
            if j > 0:
                self.steps[j].set_prev(self.steps[j - 1])
            if j < len(steps) - 1:
                self.steps[j].set_next(self.steps[j + 1])
        for i in self.steps:
            i.solve_inout()
        for j, i in enumerate(self.steps[:-1]):
            if i.input is None and j == 0:
                msg = "No input for first pipeline step!"
                raise RuntimeError(msg)
            elif i.input is None:
                i.set_input(self.steps[j - 1].output)
            if i.output is None:
                if i.get_output_type() not in self.steps[j + 1].get_input_types_valid():
                    msg = "Output of step {} not valid for step {}".format(i.name, self.steps[j + 1].name)
                    raise ValueError(msg)
                if self.steps[j + 1].output is not None and j + 2 == len(self.steps):
                    i.set_output(self.steps[j + 1].output)
                else:
                    i.set_output(FileRef(i.input.tag, i.get_output_type(), FileUse.OUTPUT, i))
        for i in self.steps:
            for j in i.get_products():
                for k in i.get_dependencies_for(j):
                    if k.use == FileUse.INPUT:
                        self.all_inputs.add(k)

    def modification_date(self, fileref):
        try:
            return os.path.getmtime(os.path.join(self.root, fileref.to_str()))
        except OSError:
            return 0

    def step_needs_executing(self, step):
        for product in step.get_products():
            mtime = self.modification_date(product)
            if any(mtime <= self.modification_date(x) for x in step.get_dependencies_for(product)):
                return True
        return False

    def get_jobs(self, step):
        products = step.get_products()

        def is_valid():
            for p in products:
                xx = products.index(p)
                for j in step.get_dependencies_for(p):
                    if j in products and products.index(j) > xx:
                        return False
            return True

        circular_test = 0
        while not is_valid():
            circular_test += 1
            for p in products[:]:
                xx = products.index(p)
                for j in step.get_dependencies_for(p):
                    if j in products and products.index(j) > xx:
                        idx = products.index(j)
                        products.remove(p)
                        products.insert(idx, p)
                        break
            if circular_test > 200:
                msg = "Circular dependency detected."
                raise OverflowError(msg)
        resultant_commands = []
        for product in products:
            mtime = self.modification_date(product)
            if any(mtime <= self.modification_date(x) for x in step.get_dependencies_for(product)):
                cmds = step.get_command_for(product)
                for cmd in cmds:
                    for i in range(len(cmd)):
                        if type(cmd[i]) is FileRef:
                            cmd[i] = os.path.join(self.root, cmd[i].to_str())
                resultant_commands.extend(cmds)
        return resultant_commands


steps = []
