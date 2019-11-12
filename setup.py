# -*- coding=utf-8 -*-

from setuptools import setup

# version 0.1.0: 使用 jieba 分词
# version 0.2.0: 使用 pkuseg 分词，增加短语过滤规则


# setup
setup(name="phrases-extractor",
      version="0.2.0",
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
          "pkuseg"
      ],

      entry_points={
      },
)
