# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from os.path import exists, dirname, join, expanduser, isdir, abspath
from os import makedirs, mkdir
from errno import EEXIST
from sys import version_info

from tranny.exceptions import ConfigError
from tranny.app import logger

try:
    # noinspection PyUnresolvedReferences
    from configparser import RawConfigParser, NoOptionError, NoSectionError, Error
except ImportError:
    from ConfigParser import RawConfigParser as ConfigParser, NoOptionError, NoSectionError

# Import a mkdir -p equivalent
if version_info >= (3, 2):
    def mkdirp(path):
        # noinspection PyArgumentList
        return makedirs(path, exist_ok=True)
else:
    def mkdirp(path):
        try:
            makedirs(path)
        except OSError as err:  # Python >2.5
            if err.errno == EEXIST and isdir(path):
                pass
            else:
                raise


class Configuration(ConfigParser):
    """
    Extend the built in ConfigParser module to provide some helper functions specific
    to tranny's configuration
    """
    _config_path = None

    def __init__(self):
        ConfigParser.__init__(self)

        self.config_file = abspath(join(dirname(dirname(__file__)), "tranny.ini"))
        try:
            loaded = self.read([self.config_file])
            if not len(loaded) == 1:
                raise ConfigError("Failed to load configuration")
        except IOError:
            raise ConfigError("No config file found: {}".format(self.config_file))

    def rules(self):
        pass

    def read(self, file_names):
        """Read and parse a filename or a list of filenames.

        This function only add debug logging output, otherwise its the same as
        ConfigParser.read.

        :return: Return list of successfully read files.
        :rtype: []unicode
        """
        loaded = ConfigParser.read(self, file_names)
        #map(logger.debug, loaded)
        return loaded

    def get_default(self, section, option, default=False, cast=None):
        """ Fetch a config value from the database with an optional default value to use
        if the config does not exist.

        :param section:
        :type section: unicode
        :param option:
        :type option: unicode
        :param default:
        :type default: unicode, int
        :param cast:
        :type cast: callable
        :return:
        :rtype: value
        """
        try:
            value = self.get(section, option)
        except (NoSectionError, NoOptionError):
            value = default
        if cast and callable(cast):
            return cast(value)
        return value

    @staticmethod
    def find_config(config_name="tranny.ini"):
        """ Attempt to find a configuration file to load. This function first attempts
         the users home directory standard location (~/.config/tranny). If that fails it
         moves on to configuration files in the source tree root directory.

        :param config_name: Path of the config file
        :type config_name: unicode
        :return:
        :rtype:
        """
        # Try and get home dir config
        home_config = expanduser("~/.config/tranny/{0}".format(config_name))
        if exists(home_config):
            return home_config

        # Try and get project source root config
        base_path = dirname(dirname(__file__))
        config_path = join(base_path, config_name)
        if exists(config_path):
            return config_path

        # No configs were found
        return False

    def create_dirs(self, path="~/.tranny"):
        """ Initialize a users config directory by creating the prerequisite directories.

        :return:
        :rtype:
        """
        config_path = expanduser(path)
        if not exists(config_path):
            mkdirp(config_path)

    def initialize(self, file_path=False):
        self.create_dirs()
        if not file_path:
            file_path = self.find_config()
        try:
            self.read(file_path)
        except OSError:
            raise ConfigError("No suitable configuration found")

    def find_sections(self, prefix):
        sections = [section for section in self.sections() if section.startswith(prefix)]
        return sections

    @property
    def rss_feeds(self):
        return map(self.get_feed_config, self.find_sections("rss_"))

    def get_feed_config(self, section, def_interval=300):
        try:
            name = self.get(section, "name")
        except NoOptionError:
            name = section.split("_", 1)[1]
        try:
            interval = self.getint(section, "interval")
        except NoOptionError:
            interval = def_interval
        rss_conf = {
            'name': name,
            'interval': interval,
            'enabled': self.getboolean(section, "enabled"),
            'url': self.get(section, "url")
        }
        return rss_conf

    def build_regex_fetch_list(self, section=None, key_name="shows"):
        """
        unused?

        :param section:
        :type section:
        :param key_name:
        :type key_name:
        :return:
        :rtype:
        """
        from tranny.parser import normalize

        if section:
            name_list = [normalize(name) for name in self.get(section, key_name).split(",")]
        else:
            name_list = [self.build_regex_fetch_list(s, key_name) for s in self.find_sections("section_")]
        return [name for name in name_list if name]

    @staticmethod
    def get_unique_section_name(section_name, sep="_"):
        try:
            return sep.join(section_name.split(sep)[1:])
        except Exception:
            return section_name

    def get_download_path(self, section, release_name):
        from .parser import parse_release
        dl_path = self.get(section, "dl_path")
        #if not exists(dl_path):
        #    raise IOError("Invalid download path root: {0}".format(dl_path))
        dir_name = parse_release(release_name)
        full_dl_path = join(dl_path, dir_name)
        if not exists(full_dl_path):
            try:
                mkdir(full_dl_path)
            except OSError:
                # Cant create presumably remote directory?
                pass
        return full_dl_path

    def get_db_path(self):
        """ Get the path to the history db used by the shelve module

        :return:
        :rtype:
        """
        return abspath(join(dirname(dirname(__file__)), "history.db"))

    def get_proxies(self):
        proxies = {}
        try:
            if self.getboolean("proxy", "enabled"):
                proxy = self.get("proxy", "server")
                if proxy:
                    proxies['http'] = proxy
                    proxies['https'] = proxy
        except (NoSectionError, NoOptionError):
            pass
        finally:
            return proxies

    def get_filters(self, section, quality):
        try:
            titles = self.get(section, "quality_{}".format(quality)).split(",")
            return self._normalize_filter_names(titles)
        except (NoSectionError, NoOptionError):
            return []

    def set_filters(self, section, quality, titles):
        """ Update the config file with new filters for a section/quality filter

        :param section: Config section
        :type section: string
        :param quality: Quality keyword (sd/hd)
        :type quality: string
        :param titles: A list of titles used for the filter ['Show A', 'Show B']
        :type titles: string[]
        :return: Save status
        :rtype: bool
        """
        titles = sorted(self._normalize_filter_names(titles))
        self.set(section, "quality_{}".format(quality), ", ".join(titles))
        return self.save()

    def _normalize_filter_names(self, titles):
        return map(self.normalize_title, titles)

    @staticmethod
    def normalize_title(title):
        """ Normalize a title string into a format more suitable for comparisons

        :param title: Title to normalize
        :type title: string
        :return: Normalized title
        :rtype: string
        """
        return " ".join([part.capitalize() for part in title.replace(".", " ").split()])

    def save(self):
        try:
            with open(self.config_file, 'w') as config:
                self.write(config)
        except IOError:
            logger.exception("Failed to write config file")
            return False
        else:
            return True

    def get_section_values(self, section):
        """ Get all values stored in the config file related to a section. Hopefully
        returning correctly python typed versions of the values based on the keywords.

        :param section: Config section name
        :type section: string
        :return: dict of section key/value pairs
        :rtype: dict
        """
        values = {}
        for key in self.options(section):
            try:
                if key == "enabled":
                    values[key] = self.getboolean(section, key)
                elif self.is_int(self.get(section, key)):
                    values[key] = self.getint(section, key)
                else:
                    values[key] = self.get(section, key)
            except (NoOptionError, NoSectionError):
                pass
        return values

    def is_int(self, value):
        """ Make a guess if the config value is a integer.

        :param value: Value to check
        :type value: string
        :return: True on int value
        :rtype: bool
        """
        try:
            int(value)
        except ValueError:
            return False
        else:
            return True

    def init_app(self, app):
        """ Load the config values defined for flask into the flask application instance

        :param app: Flask application instance to initialize
        :type app: Flask
        """
        def conv_value(k, v):
            if k in ['sqlalchemy_pool_size', 'sqlalchemy_pool_timeout', 'sqlalchemy_pool_recycle']:
                return int(v)
            if k in ['sqlalchemy_echo']:
                return v.lower() != 'false'
            return v
        config_values = {k.upper(): conv_value(k, v) for k, v in self.get_section_values("flask").items()}
        app.config.update(config_values)
        app.logger.info("Loaded config")
