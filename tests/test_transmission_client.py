from unittest import TestCase, main
from os.path import join, dirname
from tranny.client.transmission import TransmissionClient
from tranny import init_config
from tests import get_fixture


class TransmissionClientTest(TestCase):
    def setUp(self):
        self.test_file_1 = join(dirname(__file__), 'test_data', 'CentOS-6.3-x86_64-bin-DVD1to2.torrent')
        self.client = TransmissionClient(init_config(get_fixture("test_config.ini")))

    def tearDown(self):
        for torrent in self.client.list():
            self.client.remove(torrent)

    def test_add_by_uri(self):
        torrent = self.client.add(open(self.test_file_1, "rb").read(), "CentOS-6.3")
        torrent_id = torrent.keys()[0]
        self.assertTrue(torrent_id in self.client.info(torrent_id))


if __name__ == '__main__':
    main()
