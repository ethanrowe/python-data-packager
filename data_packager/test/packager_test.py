from nose import tools
import subprocess
import tempfile
import os
import shutil
import sys
import data_packager as pkg

TESTDIR = os.path.dirname(os.path.realpath(__file__))
BASEDIR = os.path.dirname(os.path.dirname(TESTDIR))
FIXTURE = os.path.join(TESTDIR, 'test-fixture-package')
FIXTURE_ALTPATH = 'alt_resources'

ENV = {'PYTHONPATH': BASEDIR}

def in_tempdir(function):
    def wrapper(*args, **kw):
        path = tempfile.mkdtemp()
        cwd = os.path.realpath('.')
        try:
            os.chdir(path)
            function(*args, **kw)
        finally:
            shutil.rmtree(path)
            os.chdir(cwd)
    wrapper.__name__ = function.__name__
    return wrapper

def with_virtualenv(function):
    @in_tempdir
    def wrapper(*args, **kw):
        venv = os.path.realpath('test-virtualenv')
        subprocess.check_call([
            sys.executable,
            '-c',
            "import sys; import pkg_resources; sys.exit(pkg_resources.load_entry_point('virtualenv', 'console_scripts', 'virtualenv')())",
            venv,
        ])
        os.chdir(BASEDIR)
        subprocess.check_call([
            vpython(venv),
            'setup.py',
            'develop',
        ])
        os.chdir(os.path.realpath(os.path.join(venv, '..')))
        return function(*(args + (venv,)), **kw)
    wrapper.__name__ = function.__name__
    return wrapper

def vpython(venv):
    return os.path.join(venv, 'bin', 'python')

def vpip(venv):
    return os.path.join(venv, 'bin', 'pip')

def with_fixture(function):
    @with_virtualenv
    def wrapper(*args, **kw):
        venv = args[-1]
        # Copy the test fixture into the tempdir,
        # and symlink its FIXTURE_ALTPATH as a sibling for path-based tests.
        shutil.copytree(FIXTURE, os.path.basename(FIXTURE))
        os.symlink(os.path.join(os.path.basename(FIXTURE), FIXTURE_ALTPATH), FIXTURE_ALTPATH)
        os.chdir(os.path.basename(FIXTURE))
        # Uses write_manifest, write_setup, and write_module
        # of the Builder class to produce files for setuptools
        # to do a proper sdist.
        subprocess.check_call([
            vpython(venv),
            '-c',
            '; '.join([
                'import data_packager as p',
                'b = p.Builder("tfp")',
                'b.write_setup(name="test-fixture-package", version="0.0.1", author="Ethan Rowe", author_email="ethan@the-rowes.com", description="Foo", long_description="fooFoo")',
                'b.write_manifest()',
                'b.write_module()',
                ]),
            ],
        )
        # Now builds the source distribution installable by pip.
        subprocess.check_call([
            vpython(venv),
            'setup.py',
            'sdist'],
        )
        # And install that source dist using the venv's pip.
        os.chdir('..')
        subprocess.check_call([
            vpip(venv),
            'install',
            os.path.join(os.path.basename(FIXTURE), 'dist', 'test-fixture-package-0.0.1.tar.gz')],
        )
        return function(*args, **kw)
    wrapper.__name__ = function.__name__
    return wrapper

def do_operation(venv, script):
    cmd = [
            vpython(venv),
            '-c',
            'import tfp; %s' % script,
        ]
    print "Command:", ' '.join(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutdata, stderrdata = p.communicate()
    if p.wait() != 0:
        raise Exception, "Return code was non-zero: " + stderrdata
    return stdoutdata

def resource_query(venv, function, argument):
    result = do_operation(venv, "import pkg_resources as p; print repr(p.%s('tfp', '%s'))" % (function, argument))
    return eval(result)

def pkg_operation(venv, script):
    return do_operation(venv, 'm = tfp.AssetManager(); %s' % script)

def dir_operation(venv, path, script):
    script = "m = tfp.AssetManager('%s'); %s" % (path, script)
    return do_operation(venv, script)

def flex_operation(venv, script, path=None):
    args = [venv, script]
    op = pkg_operation
    if path:
        args.insert(1, path)
        op = dir_operation
    return op(*args)

class TestPackager(object):
    @with_fixture
    def test_package_filename(self, venv):
        expect_a = resource_query(venv, 'resource_filename', 'assets/asset_a.txt')
        expect_b = resource_query(venv, 'resource_filename', 'assets/asset_b.txt')
        tools.assert_equal(
                expect_a + "\n",
                pkg_operation(venv, 'print m.filename("asset_a.txt")'))
        tools.assert_equal(
                expect_b + "\n",
                pkg_operation(venv, 'print m.filename("asset_b.txt")'))

    @with_fixture
    def test_dir_filename(self, venv):
        expect_a = os.path.realpath(os.path.join('foo', 'asset_a.txt'))
        expect_b = os.path.realpath(os.path.join('foo', 'asset_b.txt'))
        tools.assert_equal(
                expect_a + "\n",
                dir_operation(venv, 'foo', 'print m.filename("asset_a.txt")'))
        tools.assert_equal(
                expect_b + "\n",
                dir_operation(venv, 'foo', 'print m.filename("asset_b.txt")'))

    def test_exists(self):
        @with_fixture
        def check(p, a, x, venv):
            result = flex_operation(venv, "print repr(m.exists('%s'))" % a, p)
            tools.assert_equal(x, eval(result))

        for asset, expectation in (('asset_a.txt', True), ('not_real.txt', False)):
            for path in (None, FIXTURE_ALTPATH):
                yield check, path, asset, expectation

    def test_list(self):
        @with_fixture
        def check(expectation, path, venv):
            tools.assert_equal(
                    sorted(expectation),
                    sorted(eval(flex_operation(venv, "print repr(m.list())", path))))

        for exp, path in (
                (['asset_a.txt', 'asset_b.txt', 'package_asset'], None),
                (['asset_a.txt', 'asset_b.txt', 'directory_asset'], FIXTURE_ALTPATH)):
            yield check, exp, path

    @with_fixture
    def test_string_pkg(self, venv):
        expect = resource_query(venv, 'resource_string', 'assets/asset_a.txt')
        result = flex_operation(venv, "print repr(m.string('asset_a.txt'))", None)
        tools.assert_equal(expect, eval(result))

    @with_fixture
    def test_string_dir(self, venv):
        expect = open(os.path.join(FIXTURE_ALTPATH, 'asset_a.txt'), 'rb').read()
        result = flex_operation(venv, "print repr(m.string('asset_a.txt'))", FIXTURE_ALTPATH)
        tools.assert_equal(expect, eval(result))

    @with_fixture
    def test_stream_pkg(self, venv):
        expect = resource_query(venv, 'resource_string', 'assets/asset_b.txt')
        result = flex_operation(venv, "print repr(m.stream('asset_b.txt').read())", None)
        tools.assert_equal(expect, eval(result))

    @with_fixture
    def test_stream_dir(self, venv):
        expect = open(os.path.join(FIXTURE_ALTPATH, 'asset_b.txt'), 'rb').read()
        result = flex_operation(venv, "print repr(m.stream('asset_b.txt').read())", FIXTURE_ALTPATH)
        tools.assert_equal(expect, eval(result))

    @with_fixture
    def test_writer_dir(self, venv):
        _ = flex_operation(venv, "s = m.writer('write_asset'); s.write('some junk'); s.close()", FIXTURE_ALTPATH)
        received = open(os.path.join(FIXTURE_ALTPATH, 'write_asset'), 'rb').read()
        tools.assert_equal('some junk', received)

    @tools.raises(NotImplementedError)
    @with_fixture
    def test_writer_pkg(self, venv):
        exception = flex_operation(venv, "\ntry:\n  m.writer('write_asset')\nexcept Exception as e:\n  print repr(e)", None)
        raise eval(exception)
