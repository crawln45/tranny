# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
from time import time
from jsonrpclib import Server
from jsonrpclib.jsonrpc import ProtocolError
from tranny import app, parser, provider, datastore, release

_errors = {
    -32001: "Invalid API Key",
    -32002: "Call limit exceeded"
}


class BroadcastTheNet(provider.TorrentProvider):
    """
    Provides access to content via BTN's API.
    """
    def __init__(self, config_section="service_broadcastthenet"):
        super(BroadcastTheNet, self).__init__(config_section)
        self.enabled = app.config.getboolean(self._config_section, "enabled")
        self._api_token = app.config.get(self._config_section, "api_token")
        url = app.config.get(self._config_section, "url")
        self.api = Server(uri=url)
        app.logger.info("Initialized BTN Provider ({} State)".format(
            'Enabled' if self.enabled else 'Disabled')
        )

    def __call__(self, method, args=None):
        """ Make a API call to the JSON-RPC server. This method will inject the API key into the request
        automatically for each request.

        :param method: Name of method to execute
        :type method: str
        :param args: dict of arguments to send with request
        :type args: dict
        :return: Server response
        :rtype: str
        """
        result = False
        if not args:
            args = {}
        try:
            response = getattr(self.api, method)(self._api_token, args)
        except ProtocolError as err:
            self._handle_error(err)
        except socket.timeout:
            app.logger.warn("Timeout accessing BTN API")
        except socket.error as err:
            app.logger.error("There was a socket error trying to call BTN API")
        except Exception as err:
            app.logger.exception("Unknown BTN API call error occurred")
        else:
            result = response
        finally:
            return result

    def _handle_error(self, err):
        """

        :param err:
        :type err: ProtocolError
        :return:
        :rtype:
        """
        try:
            msg = _errors[int(err.message[0])]
        except KeyError:
            msg = ""
        app.logger.error("JSON-RPC Protocol error calling BTN API: {0}".format(msg))
        if err.message[0] == -32002:
            self.last_update = int(time()) + 300
            app.logger.info("Pausing for API cool down")

    def user_info(self):
        return self.__call__(b"userInfo")

    def get_torrents_browse(self, results=100):
        """

        :param results:
        :type results:
        :return:
        :rtype: dict
        """
        return self.__call__("getTorrentsBrowse", results)

    def get_torrent_url(self, torrent_id):
        return self.__call__("getTorrentsUrl", torrent_id)

    def fetch_releases(self, scene_only=True):
        """ Generator which yields torrent data to be loaded into backend daemons

        :param scene_only: Only fetch scene releases
        :type scene_only: bool
        :return: Matched Downloaded torrents
        :rtype: TorrentData[]
        """
        found = []
        try:
            releases = self.get_torrents_browse(50)['torrents'].values()
        except (TypeError, KeyError) as err:
            app.logger.debug("Failed to fetch releases")
        else:
            if scene_only:
                releases = [rls for rls in releases if rls['Origin'] == "Scene"]
            for entry in releases:
                release_name = entry['ReleaseName']
                release_key = datastore.generate_release_key(release_name)
                if not release_key:
                    continue
                section = parser.match_release(release_name)
                if not section:
                    continue
                if self.exists(release_key):
                    if app.config.get_default("general", "fetch_proper", True, bool):
                        if not ".proper." in release_name.lower():
                            # Skip releases unless they are considered propers
                            app.logger.debug(
                                "Skipped previously downloaded release ({0}): {1}".format(
                                    release_key,
                                    release_name
                                )
                            )
                            continue
                dl_url = self.get_torrent_url(entry['TorrentID'])
                torrent_data = self._download_url(entry['DownloadURL'])
                if not torrent_data:
                    app.logger.error("Failed to download torrent data from server: {0}".format(entry['link']))
                    continue
                data = release.TorrentData(str(release_name), torrent_data, section)
                found.append(data)
        return found
