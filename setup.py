from setuptools import setup, find_packages
import os

version = '2.0.2.dev0'

setup(name='rer.groupware.notify',
      version=version,
      description="Notification for RER Groupware",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.rst")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 4.2",
        "Programming Language :: Python",
        ],
      keywords='plone plonegov groupware rer notification rule mail',
      author='RedTurtle Technology',
      author_email='sviluppoplone@redturtle.it',
      url='https://github.com/PloneGov-IT/rer.groupware.notify',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['rer', 'rer.groupware'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.stringinterp',
          'collective.stringinterp.text',
          'rer.groupware.room',
          'Products.SimpleGroupsManagement',
          'plone.api'
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
