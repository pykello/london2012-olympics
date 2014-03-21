from setuptools import setup, find_packages

version = '0.1'

setup(
    name="olympics-tools",
    version=version,
    author='Hadi Moshayedi',
    author_email='hadi@moshayedi.net',
    license='Apache',
    packages=[],
    install_requires=[
        "jinja2",
        "lxml",
    ]
)
