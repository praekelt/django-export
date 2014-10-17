from setuptools import setup, find_packages

setup(
    name='django-export',
    version='1.0.3',
    description='Django app allowing for filtered exporting of model data.',
    long_description=open('README.rst', 'r').read() + open('AUTHORS.rst', 'r').read() + open('CHANGELOG.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekelt.com',
    url='http://github.com/praekelt/django-export',
    packages=find_packages(),
    install_requires=[
        'django-object-tools>=1.0',
        'pyyaml>=3.11'
    ],
    tests_require=[
        'django-setuptest>=0.1',
    ],
    include_package_data=True,
    test_suite="setuptest.setuptest.SetupTestSuite",
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    zip_safe=False,
)
