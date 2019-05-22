# -*- coding=utf-8 -*-

from setuptools import setup


# setup
setup(name="phrases-extractor",
      version="0.1.0",
      url="https://github.com/dongrixinyu/phrases_extractor",
      author="dongrixinyu",
      author_email="dongrixinyu.89@163.com",
      
      py_modules=[],
      packages=[
            "phrases_extractor",
      ],

      include_package_data=True,
      package_data={
            '': ['*.dict']
      },

      install_requires=[
          "jieba"
      ],

      entry_points={
      },
)
