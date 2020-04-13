from setuptools import setup

setup(name='vedirect-jmfife',
      version='0.2',
      description='Victron VE.Direct decoder for Python, forked from karioja',
      url='https://github.com/jmfife/vedirect',
      author='Janne Kario and Mike Fife',
      author_email='',
      license='MIT',
      packages=['vedirect'],
      install_requires=[
          'pyserial',
      ],
      zip_safe=False)
