from setuptools import setup, find_packages

setup(name='estrella',
      version='0.0.1',
      description='explicit semantic text representation library',
      url='http://github.com/semanchester/estrella',
      author='Semantic Computing, University of Manchester',
      author_email='viktor.schlegel@postgrad.manchester.ac.uk',
      license='MIT',
      packages=find_packages(),
      package_data={"estrella": ["resources/*.conf"]},
      zip_safe=False)
