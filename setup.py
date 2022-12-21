import re
from setuptools import setup

with open('requirements.txt') as handle:
    contents = handle.read().split('\n')

requires = []
links = []
regex = '.*#egg=(?P<package>[A-Za-z]+).*'
for content in contents:
    match = re.match(regex, content)
    if match:
        package = match.group('package')
        if package == 'pki':
            requires.append('pki-tools')
        else:
            requires.append(package)
        links.append(content.replace('-e ', ''))
    else:
        requires.append(content)

print('requires: {}'.format(requires))
print('links: {}'.format(links))

setup(
    name='vRAclient',
    version='1.0.1',
    author='Emilio Reyes',
    author_email='emilio.reyes@intel.com',
    package_dir={
        '': 'src/main/python'
    },
    packages=[
        'vRAclient'
    ],
    url='https://github.intel.com/ase-internal/vRAclient',
    description='A Python client for vRA REST API',
    install_requires=requires,
    dependency_links=links
)
