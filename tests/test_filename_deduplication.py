from ckanext.packagezip.util import FilenameDeduplicator

from nose.tools import assert_equals

class TestFilenameDeduplication(object):
    def test_first_file(self):
        fd  = FilenameDeduplicator()
        assert_equals(fd.deduplicate('index.html'), 'index.html')

    def test_second_file(self):
        fd  = FilenameDeduplicator()
        assert_equals(fd.deduplicate('index.html'), 'index.html')
        assert_equals(fd.deduplicate('robots.txt'), 'robots.txt')

    def test_duplicate(self):
        fd  = FilenameDeduplicator()
        assert_equals(fd.deduplicate('index.html'), 'index.html')
        assert_equals(fd.deduplicate('index.html'), 'index1.html')

    def test_no_extension(self):
        fd  = FilenameDeduplicator()
        assert_equals(fd.deduplicate('index'), 'index')
        assert_equals(fd.deduplicate('index'), 'index1')

    def test_reset(self):
        fd  = FilenameDeduplicator()
        assert_equals(fd.deduplicate('index.html'), 'index.html')
        fd.reset()
        assert_equals(fd.deduplicate('index.html'), 'index.html')
