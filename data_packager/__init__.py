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
    """Manages access to packaged data files.

    Given a set of data files distributed with an installable
    package as package data (the "package_data" option of
    `setuptools.setup()`), with a specific directory under that
    package for the data, access those assets easily through
    the `AssetManager`.

    Additionally, for experimenting with different data within those
    files, instantiate `AssetManager` with a directory path parameter,
    and `AssetManager` will work with assets within that directory rather
    than those distributed with the package.

    Applications can use versioned data distributed via installable
    package and use configuration to determine whether to override the
    installed data or not.

    The AssetManager by default uses its `PACKAGE` member to
    determine the package name under which the assets are distributed.

    It uses its `ASSETS_DIRECTORY` member to determine the name of the
    subdirectory within the `PACKAGE` under which assets are located.

    While a subclass needs to specify its own `PACKAGE`, the
    `ASSETS_DIRECTORY` defaults to "assets.  So, given a subclass with
    `PACKAGE` "foo", the actual assets would be expected to live under
    "foo/assets".
    """

    PACKAGE = None
    ASSETS_DIRECTORY = DEFAULT_ASSETS_SUBDIRECTORY

    def __init__(self, assets_path=None):
        """Initialize the `AssetManager`.

        If an `assets_path` is provided, it will be used the directory in
        which assets reside.

        Otherwise, assets will be assumed to live under the installed package,
        and accessed via the `pkg_resources` utilities.
        """
        if assets_path:
            self._manager = _PathManager(self.PACKAGE, os.path.realpath(assets_path))
        else:
            self._manager = _PackageManager(self.PACKAGE, self.ASSETS_DIRECTORY)


    def filename(self, asset):
        """Return the real file system path to the given `asset`."""
        return self._manager.filename(asset)

    def exists(self, asset):
        """Return True if the given `asset` exists."""
        return self._manager.exists(asset)

    def list(self):
        """Returns a list of entries within the assets directory."""
        return self._manager.list(None)

    def string(self, asset):
        """Returns the contents of requested `asset` as a string."""
        return self._manager.string(asset)

    def stream(self, asset):
        """Returns a read-only file-like handle to the requested `asset`."""
        return self._manager.stream(asset)

    def writer(self, asset):
        """Returns a write-only file handle to the requested `asset`.

        This is only supported when using a specified directory; when using
        data in the package, it will throw a `NotImplementedError`.
        """
        return self._manager.writer(asset)

    @classmethod
    def get_builder(cls):
        """Classmethod returning a new `Builder` bound to the class' settings.

        The `Builder` instance will always have its `assets_directory` explicitly
        set, regardless of whether the `AssetManager`'s `ASSETS_DIRECTORY is
        the default or not.
        """
        return Builder(cls.PACKAGE, cls.ASSETS_DIRECTORY)

class Builder(object):
    """Package developer utility class.

    The `Builder` provides some metaprogramming methods
    and code generator methods that can aid when building out
    a new `data_packager`-derived package.

    Scripts could be set up fairly easily to manage the generation
    of the files needed for the packaged data to work properly
    with `setuptools`, using the utilities provided here.
    """

    def __init__(self, package, assets_subdir=None):
        """Initialize the `Builder`.

        The `package` is the package name that should get the
        `data_packager` behaviors.  It is analogous to the
        `PACKAGE` member of the `AssetManager` class, and will be
        assigned to the `package` attribute of the `Builder` instance.

        The `assets_subdir` is the name of the directory under the
        specified `package` in which assets are expected to reside.
        If not provided, it defaults to "assets".  The value will be
        assigned to the `assets_directory` of the `Builder` instance.
        """
        self.package = package
        if assets_subdir is None:
            self.assets_directory = DEFAULT_ASSETS_SUBDIRECTORY
            self._explicit_assets_directory = False
        else:
            self.assets_directory = assets_subdir
            self._explicit_assets_directory = True


    def get_manifest_rules(self, exclude_hidden_files=True):
        """Produce the list of rules appropriate for a `MANIFEST.in` file.

        Parameters:
            exclude_hidden_files: if True (the default), the rules will
                include a rule to exclude any hidden files (files that start
                with ".") within the assets path.  If False, that rule will
                not be present.

        Returns:
            a list of strings that correspond to the lines of a
            `MANIFEST.in` file appropriate for the `package` and
            `assets_subdir` of the `Builder` instance.
        """
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
        """Produce the keyword parameters appropriate for `setuptools.setup()`.

        The following parameters will be merged with `**kwargs`:
            package_data: an entry will be made for the `Builder`'s `package`,
                to include data under the `Builder`'s `assets_directory`.  If
                an entry already exists, it will be expanded.

            packages: an entry will be made to include the `Builder`'s `package`.
                If packages are already listed, they'll be expanded, unless
                the package is already present.

            install_requirements: all requirements in `INSTALL_REQUIREMENTS`
                will be accounted for here; if a list of requirements is already
                present, it will be expanded as needed.

        The `install_requirements` expansion uses a pattern match; it does not
        enforce a specific version of its requirements, only that the requirement
        name is present.

        Parameters:
            **kwargs: the keyword parameters for `setuptools.setup()` into which
                the `Builder`-specific parameters will be merged.

        Returns:
            A dictionary of keyword parameters appropriate for passing to
            `setuptools.setup()` that enforces the configuration needs for
            a `data_packager` using the `Builder`'s attributes, merged with
            caller-provided parameters.
        """
        kwargs['package_data'] = self.merge_package_data(kwargs.get('package_data', {}))
        kwargs['packages'] = self.merge_packages(kwargs.get('packages', []))
        kwargs['install_requires'] = self.merge_install_requires(kwargs.get('install_requires', []))
        return kwargs

    def get_asset_manager_class(self):
        """Produces a new `AssetManager` subclass.

        The `AssetManager` subclass returned will be bound to
        the `Builder`'s `package` and `assets_directory`.  The
        `assets_directory` will only be explicitly specified on the
        subclass if it was explicitly provided to the `Builder`
        at initialization.
        """
        cls_const = {'PACKAGE': self.package}
        if self._explicit_assets_directory:
            cls_const['ASSETS_DIRECTORY'] = self.assets_directory
        return type('AssetManager', (AssetManager,), cls_const)

    def write_setup(self, setup_path='setup.py', **kwarg):
        """Produces a `setuptools` setup file.

        This uses `get_setup_parameters` to produce the set of keyword
        params for the resulting `setuptools.setup()` call, merging with
        `**kwarg` per usual.

        The file written will be determined by `setup_path`.
        """
        import pprint
        with open(setup_path, 'w') as f:
            print >> f, 'import setuptools'
            print >> f, ''
            f.write('param = ')
            pprint.pprint(self.get_setup_parameters(**kwarg), stream=f, indent=4)
            print >> f, ''
            print >> f, 'setuptools.setup(**param)'

    def write_manifest(self, manifest_path='MANIFEST.in', exclude_hidden_files=True):
        """Produces a `MANIFEST.in` file.

        Uses the `get_manifest_rules` method to produce the appropriate
        rules for this data package, and writes them out to the `manifest_path`
        specified.

        Passes through `exclude_hidden_files` to the underlying `get_manifest_rules`
        call.
        """
        with open(manifest_path, 'w') as f:
            for rule in self.get_manifest_rules(exclude_hidden_files):
                print >> f, rule

    def write_module(self, path=None):
        """Produces a module file for an data package manager.

        Writes a python module file to `path` that will have
        an `AssetManager` subclass (named `AssetManager` within
        the module) bound to the settings of the `Builder` instance.

        If `path` is unspecified, it will go to "__init__.py" of
        the `Builder`'s `package`, which needs to be a package (or
        subpackage) and not a simple module since the managed assets
        are expected to reside in a subdirectory within.

        The resulting module will have `AssetManager` and nothing else.
        """
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

