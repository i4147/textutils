import os
import shutil
import subprocess
from threading import Lock
from watchdog.events import FileSystemEventHandler
from .fileref import FileRef, FileUse, to_fref
from .pipeline import Sink

SEV_ERROR = 1
SEV_INFO = 2
SEV_DBG = 3


class Textle(FileSystemEventHandler):
    def __init__(self, pipelines, global_options, root_dir):
        self.pipelines = pipelines
        self.global_options = {"layout": "bin", "build_dir": ".textle", "parallel": 0, "externals": []}
        self.global_options.update(global_options)
        if type(self.global_options["externals"]) is not list:
            self.global_options["externals"] = [self.global_options["externals"]]
        self.root_dir = os.path.abspath(root_dir)
        for j in range(len(self.global_options["externals"])):
            self.global_options["externals"][j] = os.path.join(self.root_dir, self.global_options["externals"][j])
        self.layout_roots()
        self.job_callback = lambda x, y, z: None
        self.build_lock = Lock()

    def with_job_callback(self, cb):
        self.job_callback = cb
        return self

    def layout_roots(self):
        if self.global_options["layout"] == "flat":
            for i in self.pipelines:
                i.root = self.root_dir
        elif self.global_options["layout"] in ["bin", "segregated"]:
            build_dir = os.path.join(self.root_dir, self.global_options["build_dir"])
            for j, i in enumerate(self.pipelines):
                if self.global_options["layout"] == "segregated":
                    i.root = os.path.join(build_dir, "pipe{}".format(j))
                else:
                    i.root = build_dir

    def clean(self):
        if self.global_options["layout"] != "flat":
            shutil.rmtree(os.path.join(self.root_dir, self.global_options["build_dir"]))
        else:
            msg = "Not implemented -- todo"
            raise NotImplementedError(msg)

    def get_input_files(self):
        filrefs = set()
        for i in self.pipelines:
            filrefs.union(i.all_inputs)
        return [os.path.join(self.root_dir, x.to_str()) for x in filrefs]

    def build_pipeline(self, pipeline):
        out_file = pipeline.steps[-1].output
        self.job_callback("pipeline", SEV_INFO, "Building {}".format(out_file.to_str()))
        if self.global_options["layout"] != "flat":
            self.job_callback("copy:in", SEV_DBG, "Copying input")
            for in_ in pipeline.all_inputs:
                self.job_callback("copy:in", SEV_DBG, "Copying input {}".format(in_.to_str()))
                try:
                    if not os.path.exists(os.path.split(os.path.join(pipeline.root, in_.to_str()))[0]):
                        os.makedirs(os.path.split(os.path.join(pipeline.root, in_.to_str()))[0])
                except FileNotFoundError:
                    pass
                if not any(os.path.basename(x) == in_.to_str() for x in self.global_options["externals"]):
                    shutil.copy2(os.path.join(self.root_dir, in_.to_str()), os.path.join(pipeline.root, in_.to_str()))
        if self.global_options["externals"]:
            self.job_callback("copy:externals", SEV_DBG, "Copying externals")
            for ext in self.global_options["externals"]:
                self.job_callback("copy:externals", SEV_DBG, "Copying external {}".format(ext))
                if not os.path.exists(pipeline.root):
                    os.makedirs(pipeline.root)
                shutil.copy2(ext, os.path.join(pipeline.root, os.path.basename(ext)))
        did_anything = False
        for step in pipeline.steps:
            if issubclass(step, Sink):
                continue
            if pipeline.step_needs_executing(step):
                did_anything = True
                jobs_required = pipeline.get_jobs(step)
                self.job_callback("step:{}".format(step.name), SEV_DBG, "Got jobs")
                for job in jobs_required:
                    cwd = os.getcwd()
                    try:
                        os.chdir(pipeline.root)
                        output = subprocess.check_output(job, stderr=subprocess.PIPE, universal_newlines=True)
                        self.job_callback(
                            "job:{}:{}".format(step.name, job[0]),
                            SEV_INFO,
                            "Command {} finished sucessfully".format(" ".join(job)),
                        )
                    except subprocess.CalledProcessError as e:
                        self.job_callback(
                            "job:{}:{}".format(step.name, job[0]),
                            SEV_ERROR,
                            "Command {} exited with code {}.".format(" ".join(job), e.returncode),
                        )
                        raise
                    finally:
                        os.chdir(cwd)
                self.job_callback("step:{}".format(step.name), SEV_DBG, "Finished OK")
        if not did_anything:
            return
        if self.global_options["layout"] != "flat":
            self.job_callback("copy:out", SEV_DBG, "Copying output {}".format(out_file.to_str()))
            shutil.copy(os.path.join(pipeline.root, out_file.to_str()), os.path.join(self.root_dir, out_file.to_str()))
        self.job_callback("pipeline", SEV_INFO, "Built {}".format(out_file.to_str()))

    def build(self, from_file_change=None):
        if from_file_change is not None:
            fref = to_fref(os.path.relpath(from_file_change, self.root_dir), FileUse.INPUT)
            for i in self.pipelines:
                if fref in i.all_inputs:
                    self.build_pipeline(i)
        else:
            for i in self.pipelines:
                self.build_pipeline(i)

    def on_modified(self, event):
        if not os.path.isfile(event.src_path):
            return
        with self.build_lock:
            self.build(event.src_path)
