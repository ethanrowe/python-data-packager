from nose import tools
import mock
import data_packager as pkg

ASSET_DIR = 'assets'

def get_mocks():
    return str(mock.Mock(name='MockPackage')), str(mock.Mock(name='MockAssets'))

def get_mocked_builder():
    n, a = get_mocks()
    return pkg.Builder(n, a), n, a

class TestBuilderClass(object):
    def test_initialization(self):
        for args in (
                ('pkg_one',),
                ('pkg_two', 'foodir'),
            ):
            yield self.check_initialization, args

    def check_initialization(self, constr_args):
        b = pkg.Builder(*constr_args)
        tools.assert_equal(constr_args[0], b.package)
        tools.assert_equal(constr_args[1] if len(constr_args) > 1 else ASSET_DIR, b.assets_directory)

    def test_manifest_rules(self):
        b, n, a = get_mocked_builder()
        pattern = "%s/%s" % (n, a)
        tools.assert_equal(
                ["recursive-include %s *" % pattern, "recursive-exclude %s \\.*" % pattern],
                b.get_manifest_rules())

    def test_manifest_rules_no_hidden(self):
        b, n, a = get_mocked_builder()
        pattern = "%s/%s" % (n, a)
        tools.assert_equal(
                ["recursive-include %s *" % pattern],
                b.get_manifest_rules(False))

    def test_setup_parameters_basic(self):
        b, n, a = get_mocked_builder()
        param = {'foo': 'bar', 'blee': 'blah'}
        result = b.get_setup_parameters(**param)
        tools.assert_equal(
                dict(param.items() + [
                    ('packages', [n]),
                    ('package_data', {n: ['%s/*' % a]}),
                    ('install_requires', ['data_packager'])]),
                result)

    def test_setup_parameters_merge_packages(self):
        b, n, a = get_mocked_builder()
        result = b.get_setup_parameters(packages=['foo', 'foo.bar'])
        tools.assert_equal(
                {'packages': ['foo', 'foo.bar', n],
                 'package_data': {n: ['%s/*' % a]},
                 'install_requires': ['data_packager']},
                result)

    def test_setup_parameters_merge_redundant_packages(self):
        b, n, a = get_mocked_builder()
        result = b.get_setup_parameters(packages=['foo', n, 'foo.bar'])
        tools.assert_equal(
                {'packages': ['foo', n, 'foo.bar'],
                 'package_data': {n: ['%s/*' % a]},
                 'install_requires': ['data_packager']},
                result)


    def test_setup_parameters_merge_package_data(self):
        b, n, a = get_mocked_builder()
        result = b.get_setup_parameters(package_data={'foo': ['blah'], n: ['blee']})
        tools.assert_equal(
                {'packages': [n],
                 'package_data': {'foo': ['blah'], n: ['blee', '%s/*' % a]},
                 'install_requires': ['data_packager']},
                result)

    def test_setup_parameters_merge_install_requires(self):
        b, n, a = get_mocked_builder()
        result = b.get_setup_parameters(install_requires=['foo', 'bar'])
        tools.assert_equal(
                {'packages': [n],
                 'package_data': {n: ['%s/*' % a]},
                 'install_requires': ['foo', 'bar', 'data_packager']},
                result)

    def test_get_asset_manager_class_basic(self):
        n, a = get_mocks()
        b = pkg.Builder(n)
        result = b.get_asset_manager_class()
        tools.assert_equal(True, issubclass(result, (pkg.AssetManager,)))
        tools.assert_equal(n, getattr(result, 'PACKAGE', None))
        # Verify that ASSETS_DIRECTORY inherits from parent in default case.
        with mock.patch.object(pkg.AssetManager, 'ASSETS_DIRECTORY') as m:
            tools.assert_equal(m, getattr(result, 'ASSETS_DIRECTORY', None))

    def test_get_asset_manager_class_assets_override(self):
        b, n, a = get_mocked_builder()
        result = b.get_asset_manager_class()
        tools.assert_equal(True, issubclass(result, (pkg.AssetManager,)))
        tools.assert_equal(n, getattr(result, 'PACKAGE', None))
        tools.assert_equal(a, getattr(result, 'ASSETS_DIRECTORY', None))

