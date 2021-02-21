
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE.txt') as f:
    license = f.read()

setup(
    name='ndpulsecount',
    version='0.0.1',
    description='A package to interface with the Narwhal Devices Pulse Counter',
    long_description=readme,
    author='Rory Speirs',
    author_email='rory@narwhaldevices.com',
    url='https://https://github.com/RorySpeirs/pulse-counter',
    license=license,
    packages=find_packages(),
    python_requires='>=3.8'
)

