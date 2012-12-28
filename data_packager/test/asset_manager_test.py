from nose import tools
import mock
import data_packager as pkg

def get_mocks():
    return str(mock.Mock(name='Package')), str(mock.Mock(name='Assets'))

class TestAssetManager(object):
    def test_defaults(self):
        tools.assert_equal(None, getattr(pkg.AssetManager, 'PACKAGE', mock.Mock()))
        tools.assert_equal('assets', getattr(pkg.AssetManager, 'ASSETS_DIRECTORY', None))


    def test_builder(self):
        p, a = get_mocks()
        subclass = type('Test', (pkg.AssetManager,), {'PACKAGE': p, 'ASSETS_DIRECTORY': a})
        b = subclass.get_builder()
        tools.assert_equal(True, isinstance(b, pkg.Builder))
        tools.assert_equal(p, getattr(b, 'package', None))
        tools.assert_equal(a, getattr(b, 'assets_directory', None))

