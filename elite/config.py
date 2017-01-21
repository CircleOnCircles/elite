import os

from AppKit import NSFont
# Strangely NSKeyedArchiver won't import without ScriptingBridge
import ScriptingBridge  # flake8: noqa
from Foundation import NSKeyedArchiver, NSCalibratedRGBColor
import yaml


def join_path(loader, node):
    seq = loader.construct_sequence(node)
    return os.path.join(*[i for i in seq])


def macos_font(loader, node):
    seq = loader.construct_sequence(node)

    if len(seq) != 2:
        raise ValueError('only two arguments may be provided, the font name and size')

    font_name, font_size = seq
    font = NSFont.fontWithName_size_(font_name, font_size)

    if font is None:
        raise ValueError('unable to find the font requested')

    return bytes(NSKeyedArchiver.archivedDataWithRootObject_(font))


def macos_color(loader, node):
    seq = loader.construct_sequence(node)

    if len(seq) != 4:
        raise ValueError('only four arguments may be provided, red, green, blue and alpha')

    red, green, blue, alpha = seq

    for color in [red, green, blue]:
        if not 0 <= color <= 255:
            raise ValueError('colors provided must be in the range 0 to 255')

    if not 0 <= alpha <= 1:
        raise ValueError('alpha must be in the range 0 to 1')

    color = NSCalibratedRGBColor.alloc().initWithRed_green_blue_alpha_(
        red / 255, green / 255, blue / 255, alpha
    )

    return bytes(NSKeyedArchiver.archivedDataWithRootObject_(color))


yaml.add_constructor('!join_path', join_path)
yaml.add_constructor('!macos_font', macos_font)
yaml.add_constructor('!macos_color', macos_color)


class Config(object):
    """
    Stores the combined YAML configuration for all files found in the search path.

    :param search_path: The path to search for YAML config files.
    """
    def __init__(self, search_path):
        self.search_path = search_path

        self.config_files = []
        self.config = {}

        self._find_config_files()
        self._load_configs()

    def _find_config_files(self):
        """
        Find the paths to all YAMl config files in the chosen search path and add them to the
        self.config_files list.
        """
        for root, dirs, files in os.walk(self.search_path):
            for filename in files:
                # Skip any files that aren't YAML
                extension = os.path.splitext(filename)
                if extension[1] not in ['.yml', '.yaml']:
                    continue

                # Add the config to our list
                config_path = os.path.join(root, filename)
                self.config_files.append(config_path)

    def _load_configs(self):
        """
        Load all the configs requested into one big combined data structure.  The data
        structure is stored in self.config.
        """
        configs = []
        for config_file in self.config_files:
            with open(config_file) as f:
                config_str = f.read()
                configs.append(config_str if config_str.endswith('\n') else config_str + '\n')

        self.config = yaml.load(''.join(configs))

    def __getattr__(self, variable):
        """
        Provides an easy way to obtain any top level configuration variable.

        :param variable: The config variable being requested.

        :return: The respective variable's value.
        """
        if variable in self.config:
            return self.config[variable]

        raise AttributeError(f'the config has no variable named {variable}')
