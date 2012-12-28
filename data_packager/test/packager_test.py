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
ENV = {'PYTHONPATH': BASEDIR}

def in_tempdir(function):
    def wrapper(*args, **kw):
        path = tempfile.mkdtemp()
        cwd = os.path.realpath('.')
        try:
            os.chdir(path)
            function(*args, **kw)
        finally:
            #shutil.rmtree(path)
            print "temp path", path
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
        shutil.copytree(FIXTURE, os.path.basename(FIXTURE))
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
        expect_a = os.path.join('foo', 'asset_a.txt')
        expect_b = os.path.join('foo', 'asset_b.txt')
        tools.assert_equal(
                expect_a + "\n",
                dir_operation(venv, 'foo', 'print m.filename("asset_a.txt")'))
        tools.assert_equal(
                expect_b + "\n",
                dir_operation(venv, 'foo', 'print m.filename("asset_b.txt")'))

