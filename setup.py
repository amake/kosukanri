from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='kosukanri',
    version='1.0',
    description='Summarize commits to a collection of git repositories, for time-tracking purposes',
    long_description=long_description,
    url='https://github.com/amake/kosukanri',
    author='Aaron Madlon-Kay',
    author_email='aaron@madlon-kay.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Scheduling',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='git repository time tracking productivity',
    py_modules=['kosukanri'],
    entry_points={
        'console_scripts': [
            'kosukanri=kosukanri:main',
        ],
    },
)
