import os
import pkg_resources
import re
import warnings

REQ_PATTERN = re.compile('\bdata_packager\b')
DEFAULT_ASSETS_SUBDIRECTORY = 'assets'
INSTALL_REQUIREMENTS = ['data_packager']

class _Manager(object):
    def __init__(self, package, path):
        self.package = package
        self.path = path

    def relative(self, asset):
        return os.path.join(self.path, asset)

    def writer(self, asset):
        raise NotImplementedError, "The writer operation is not supported for this AssetManager"

class _PathManager(_Manager):
    def filename(self, asset):
        return self.relative(asset)

    def exists(self, asset):
        return os.path.exists(self.relative(asset))

    def list(self, asset):
        return os.listdir(self.relative(asset) if asset else self.path)

    def string(self, asset):
        return self.stream(asset).read()

    def stream(self, asset):
        return open(self.relative(asset), 'rb')

    def writer(self, asset):
        return open(self.relative(asset), 'wb')

class _PackageManager(_Manager):
    def call(self, name, *args):
        func = getattr(pkg_resources, name)
        return func(self.package, *args)

    def filename(self, asset):
        return self.call('resource_filename', self.relative(asset))

    def exists(self, asset):
        return self.call('resource_exists', self.relative(asset))

    def list(self, asset):
        return self.call('resource_listdir',
                         self.relative(asset) if asset else self.path)

    def string(self, asset):
        return self.call('resource_string', self.relative(asset))

    def stream(self, asset):
        return self.call('resource_stream', self.relative(asset))

class AssetManager(object):
    PACKAGE = None
    ASSETS_DIRECTORY = DEFAULT_ASSETS_SUBDIRECTORY

    def __init__(self, assets_path=None):
        if assets_path:
            self._manager = _PathManager(self.PACKAGE, os.path.realpath(assets_path))
        else:
            self._manager = _PackageManager(self.PACKAGE, self.ASSETS_DIRECTORY)

    def filename(self, asset):
        return self._manager.filename(asset)

    def exists(self, asset):
        return self._manager.exists(asset)

    def list(self):
        return self._manager.list(None)

    def string(self, asset):
        return self._manager.string(asset)

    def stream(self, asset):
        return self._manager.stream(asset)

    def writer(self, asset):
        return self._manager.writer(asset)

class Builder(object):
    def __init__(self, package, assets_subdir=None):
        self.package = package
        if assets_subdir is None:
            self.assets_directory = DEFAULT_ASSETS_SUBDIRECTORY
            self._explicit_assets_directory = False
        else:
            self.assets_directory = assets_subdir
            self._explicit_assets_directory = True

    def get_manifest_rules(self, exclude_hidden_files=True):
        namespace = '%s/%s' % (self.package, self.assets_directory)
        rules = ['recursive-include %s *' % namespace]
        if exclude_hidden_files:
            rules.append('recursive-exclude %s \\.*' % namespace)
        return rules

    def merge_package_data(self, pkg_data):
        # copy
        pkg_data = dict(pkg_data.iteritems())
        entries = pkg_data.get(self.package, [])
        pkg_data[self.package] = entries + ['%s/*' % self.assets_directory]
        return pkg_data

    def merge_packages(self, pkgs):
        if self.package in pkgs:
            return pkgs
        return pkgs + [self.package]

    def merge_install_requires(self, reqs):
        reqs = list(reqs)
        def in_reqs(pattern):
            for req in reqs:
                if pattern.match(req):
                    return True
            return False

        for req in INSTALL_REQUIREMENTS:
            p = re.compile('\b%s\b' % req)
            if not in_reqs(p):
                reqs.append(req)

        return reqs

    def get_setup_parameters(self, **kwargs):
        kwargs['package_data'] = self.merge_package_data(kwargs.get('package_data', {}))
        kwargs['packages'] = self.merge_packages(kwargs.get('packages', []))
        kwargs['install_requires'] = self.merge_install_requires(kwargs.get('install_requires', []))
        return kwargs

    def get_asset_manager_class(self):
        cls_const = {'PACKAGE': self.package}
        if self._explicit_assets_directory:
            cls_const['ASSETS_DIRECTORY'] = self.assets_directory
        return type('AssetManager', (AssetManager,), cls_const)

    def write_setup(self, setup_path='setup.py', **kwarg):
        import pprint
        with open(setup_path, 'w') as f:
            print >> f, 'import setuptools'
            print >> f, ''
            f.write('param = ')
            pprint.pprint(self.get_setup_parameters(**kwarg), stream=f, indent=4)
            print >> f, ''
            print >> f, 'setuptools.setup(**param)'

    def write_manifest(self, manifest_path='MANIFEST.in', exclude_hidden_files=True):
        with open(manifest_path, 'w') as f:
            for rule in self.get_manifest_rules(exclude_hidden_files):
                print >> f, rule

    def write_module(self, path=None):
        if path is None:
            path = os.path.join(self.package, '__init__.py')
        args = [self.package]
        if self._explicit_assets_directory:
            args.append(self.assets_directory)
        args = ','.join("'%s'" % arg for arg in args)
        with open(path, 'w') as f:
            print >> f, 'import data_packager'
            print >> f, 'AssetManager = data_packager.Builder(%s).get_asset_manager_class()' % args
            print >> f, 'del data_packager'

