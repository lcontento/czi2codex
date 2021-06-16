from setuptools import setup, find_packages

setup(
    name='czi2codex',
    version='0.1.0',
    author='Erika Dudkin',
    author_email='erikadudkin@gmx.de',
    description='Covert czi-files to CODEX format',
    license='Apache-2.0 License',
    url='https://github.com/erikadudki/czi2codex',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'scikit-image',
        'aicspylibczi>=2,<3',
        'tifffile',
        'pyyaml',
        'xmltodict',
        'lxml'
    ]
)
