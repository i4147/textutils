import os
import math
import docopt
from schema import Schema, Use, And, Or
import torch
from . import __version__
from . import api, io, commands
from .logger import ansi, ConsoleLog


def validate(config):
    def split_size(size: str):
        return tuple(map(int, size.split("x")))

    def split_strings(text: str):
        return text.split(",")

    def split_floats(text: str):
        return tuple(map(float, text.split(",")))

    def split_ints(text: str):
        return tuple(map(int, text.split(",")))

    sch = Schema(
        {
            "SOURCE": [str],
            "TARGET": Or(None, str),
            "size": And(Use(split_size), tuple),
            "output": str,
            "intact": Use(bool),
            "weights": Use(split_floats),
            "zoom": Use(int),
            "variations": Use(int),
            "seed": Or(None, Use(int)),
            "mode": Or(None, "patch", "gram", "hist"),
            "octaves": Or(None, Use(int)),
            "iterations": Use(split_ints),
            "model": Or("VGG11", "VGG13", "VGG16", "VGG19"),
            "layers": Or(None, Use(split_strings)),
            "device": Or(None, "cpu", "cuda"),
            "precision": Or(None, "float16", "float32"),
            "help": Use(bool),
            "quiet": Use(bool),
            "verbose": Use(bool),
        },
        ignore_extra_keys=True,
    )
    return sch.validate({k.replace("--", ""): v for k, v in config.items()})


def main():
    config = docopt.docopt(__doc__[204:], version=__version__, help=False)
    all_commands = [cmd.lower() for cmd in commands.__all__] + ["--help"]
    command = [cmd for cmd in all_commands if config[cmd]][0]
    config = validate(config)
    sources, target, output, seed = [config.pop(k) for k in ("SOURCE", "TARGET", "output", "seed")]
    weights, zoom = [config.pop(k) for k in ("weights", "zoom")]
    log = ConsoleLog(config.pop("quiet"), config.pop("verbose"))
    log.notice(ansi.PINK + __doc__[:204] + ansi.ENDC)
    if config.pop("help") is True:
        log.notice(__doc__[204:])
        return
    resize_source = not config.pop("intact")
    for filename in sources:
        if seed is not None:
            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)
        source_arr, source_props = io.load_tensor_from_files(filename)
        target_arr = io.load_tensor_from_files(target) if target else None
        if resize_source:

            def length(s):
                return math.sqrt(s[0] * s[1])

            s = length(config["size"]) / length(source_arr.shape[2:])
            F = torch.nn.functional
            source_arr = F.interpolate(source_arr, scale_factor=s, mode="bilinear", antialias=True)
        if command == "remix":
            cmd = commands.Remix(source_arr)
        if command == "enhance":
            cmd = commands.Enhance(target_arr, source_arr, zoom=zoom)
            config["octaves"] = cmd.octaves
            config["size"] = (target_arr.size[0] * zoom, target_arr.size[1] * zoom)
        if command == "expand":
            factor = (
                target_arr.size[0] / config["size"][0],
                target_arr.size[1] / config["size"][1],
            )
            cmd = commands.Expand(target_arr, source_arr, factor=factor)
        if command == "remake":
            cmd = commands.Remake(target_arr, source_arr, weights=weights)
            config["octaves"] = 1
            config["size"] = target_arr.size
        if command == "mashup":
            cmd = commands.Mashup([source_arr, target_arr])
        if command == "repair":
            cmd = commands.Repair(target_arr, source_arr)
            config["octaves"] = 3
            config["size"] = target_arr.size
        try:
            config["output"] = output
            config["output"] = config["output"].replace("{source}", os.path.splitext(os.path.basename(filename))[0])
            if target:
                config["output"] = config["output"].replace("{target}", os.path.splitext(os.path.basename(target))[0])
            config["properties"] = source_props
            result, filenames = api.process_single_command(cmd, log, **config)
            log.notice(ansi.PINK + "\n=> result:", filenames, ansi.ENDC)
        except KeyboardInterrupt:
            print(ansi.PINK + "\nCTRL+C detected, interrupting..." + ansi.ENDC)
            break


if __name__ == "__main__":
    main()
