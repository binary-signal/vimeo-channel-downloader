from vimeodl import __version__
from vimeodl.vimeo import VimeoLinkExtractor, VimeoDownloader

def test_version():
    assert __version__ == '0.1.0'

def test_vimeo_link_extractor():
    vm = VimeoLinkExtractor()
    vm.extract()
