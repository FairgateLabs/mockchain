from setuptools import setup, find_packages

setup(
    name='mockchain',
    version='0.1.0',
    author='Ariel Futoransky',
    author_email='futo@fairgate.io',
    description='A self-contained blockchain simulator to help try ideas.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/mockchain',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)