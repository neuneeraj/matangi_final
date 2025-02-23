from setuptools import setup, find_packages

setup(
    name="matangi",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'antlr4-python3-runtime',
    ],
)