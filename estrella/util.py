import json
import logging
import logging.config
from logging.handlers import RotatingFileHandler
import os
from collections import Iterable, Mapping
from typing import List, Union

from pyhocon import ConfigFactory, ConfigTree

from estrella.exceptions.config import MalformattedConfigException
from estrella.interfaces import Readable


def setup_logging(path=''):
    """
    Setup logging configuration.
    """

    cfg = read_config(path, default="logging.conf")

    logging.config.dictConfig(cfg.as_plain_ordered_dict())

    logging.getLogger(__name__).info("Config loaded.")


class MakeFileHandler(RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)


class FQNFilter(logging.Filter):
    def __init__(self, max_len=30):
        super().__init__()
        self.max_len = max_len

    def filter(self, record):
        fqn = ".".join((record.name, record.funcName))
        if len(fqn) > self.max_len:
            fqns = fqn.split(".")
            i = 0
            while sum(len(fqn) for fqn in fqns) + len(fqns) - 1 > self.max_len and i < len(fqns):
                fqns[i] = fqns[i][0]
                i += 1
            fqn = ".".join(fqns)[:self.max_len]
        record.fqn = fqn
        return record


def read_config(path="", default="default.conf"):
    if path is None:
        path = ""
    from pkg_resources import resource_string
    default = resource_string(__name__, '/resources/{}'.format(default))
    # default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", default)
    default = default.decode("utf-8")
    try:
        with open(path, "r") as f:
            cfg_str = f.read()
    except FileNotFoundError:
        if path:
            logging.getLogger(__name__).warning("{} doesn't exist! Loading default.".format(path))
        return ConfigFactory.parse_string(default)
    cfg_str = 'include "{}"\n{}'.format(default, cfg_str)
    return ConfigFactory.parse_string(cfg_str)


def load_class(class_string: str, restrict_to: Union[type, List[type]] = None, relative_import: str = ""):
    try:
        module_name, cls_name = class_string.rsplit(".", 1)
    except ValueError:
        cls_name = class_string
        module_name = ""
    try:
        x = ".".join((relative_import, module_name)).rstrip(".")
        print(x, cls_name)
        mod = __import__(x, fromlist=cls_name)
    except ModuleNotFoundError:
        print(module_name, cls_name)
        mod = __import__(module_name, fromlist=cls_name)
    cls = getattr(mod, cls_name)

    if restrict_to:
        check_subclass(cls, restrict_to)
    return cls


def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(s for c in cls.__subclasses__() for s in get_all_subclasses(c))


def check_subclass(cls, restrict_to):
    if not isinstance(restrict_to, Iterable):
        restrict_to = [restrict_to]
    if not any(cls == target_cls or cls in get_all_subclasses(target_cls) for target_cls in restrict_to):
        raise ValueError("{} is not subclass of any of {}".format(cls, restrict_to))


def get_constructor_and_args(config):
    if not isinstance(config, ConfigTree):
        return config, dict()

    if len(config) != 2:
        raise MalformattedConfigException("Classes constructed from config accept exactly "
                                          "two entries: class and args. Was {} entries: {}".format(len(config), config))
    return config["class"], config["args"]


def safe_construct(config_or_instance,
                   restrict_to: Union[type, List[type]] = None,
                   relative_import: str = "",
                   perform_subclass_check=True):
    if isinstance(config_or_instance, ConfigTree):
        return construct_from_config(config_or_instance, restrict_to, relative_import)
    if perform_subclass_check:
        check_subclass(config_or_instance.__class__, restrict_to)
    return config_or_instance


def construct_from_config(config: ConfigTree, restrict_to: Union[type, List[type]] = None, relative_import: str = ""):
    """
    Helper function to combine load_class and construct.

    Config layout supposed to be like this:
    {class_string: args_as_cfg}
    where args_as_cfg are either dict, list or a single argument
    :param relative_import: String to prepend to the absolute import.
    :param restrict_to: Class to be constructed must be of this type(s).
    :param config: Config to parse as class.
    :return: Parsed class if possible.
    """
    logger = logging.getLogger(__name__)
    cls_name, construct_args = get_constructor_and_args(config)
    logger.debug("Class name: {} Args: {}".format(cls_name, str(construct_args)))
    cls = load_class(cls_name, restrict_to=restrict_to, relative_import=relative_import)
    return construct(cls, construct_args)


def construct(cls: type, args_as_cfg):
    """
    Default factory method for a given class and given arguments.

    Construct the class with given arguments. Arguments parameter can be a single argument, a List
    :param cls:
    :param args_as_cfg:
    :return:
    """
    logger = logging.getLogger(__name__)
    if isinstance(args_as_cfg, Mapping):
        logger.debug("Constructing {} with kwargs {}".format(cls.__name__, str(args_as_cfg)))
        return cls(**args_as_cfg)
    if isinstance(args_as_cfg, Iterable) and not isinstance(args_as_cfg, str):
        logger.debug("Constructing {} with varargs {}".format(cls.__name__, str(args_as_cfg)))
        return cls(*args_as_cfg)
    else:
        # one arg only
        logger.debug("Constructing {} with single arg {}".format(cls.__name__, str(args_as_cfg)))
        return cls(args_as_cfg)


def format_config(config):
    return json.dumps(config.as_plain_ordered_dict(), indent=4)


def pprint(*args, delimiter=" ", to_stdout=False, **kwargs):
    result = delimiter.join(arg.pprint(**kwargs) if isinstance(arg, Readable) else repr(arg) for arg in args)
    if to_stdout:
        print(result)
    return result
