"""
Setup script for Steel Quantity Takeoff
"""

from setuptools import setup, find_packages

setup(
    name='steel-takeoff',
    version='1.0.0',
    author='Sero',
    description='Extract rebar quantities from DXF construction drawings',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'ezdxf>=1.3.0',
        'pandas>=2.0.0',
        'openpyxl>=3.1.0',
        'rich>=13.0.0',
    ],
    entry_points={
        'console_scripts': [
            'steel-takeoff=cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Construction Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Civil Engineering',
    ],
)
