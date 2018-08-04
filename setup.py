from setuptools import setup, find_packages


LONG_DESCRIPTION = open('README.md').read()

INSTALL_REQUIRES = [
    'requests',
    'requests-html',
    'python-dateutil'
]

setup(
    name='timepro-utils',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Utility for programmatically getting and submitting data to Intertec TimePro (timesheets.com.au)',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='http://github.com/christippett/timepro-utils',
    author='Chris Tippett',
    author_email='c.tippett@gmail.com',
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    zip_safe=False
)