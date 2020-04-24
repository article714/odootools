from setuptools import __version__, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

if int(__version__.split(".")[0]) < 41:
    raise RuntimeError("setuptools >= 41 required to build")

setup(
    use_scm_version={
        "write_to": "src/odootools/version.py",
        "write_to_template": '__version__ = "{version}"',
    },
    python_requires=">=3.5, <4",
    install_requires=["configobj", "psycogreen"],
    setup_requires=[
        # this cannot be enabled until https://github.com/pypa/pip/issues/7778
        # is addressed "setuptools_scm >= 2"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: LGPL-3",
        "Operating System :: OS Independent",
    ],
)
