from distutils.core import setup

from catkin_pkg.python_setup import generate_distutils_setup

setup_args = generate_distutils_setup(
    packages=['wuji_retargeting', 'wuji_retargeting.opt'],
    package_dir={'': '.'},
)

setup(**setup_args)
