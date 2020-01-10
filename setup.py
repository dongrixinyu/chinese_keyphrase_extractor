# -*- coding=utf-8 -*-

from setuptools import setup

# version 0.1.0: 使用 jieba 分词，利用 word 级别 tfidf 计算
# version 0.2.0: 使用 pkuseg 分词，利用 word 级别 tfidf 计算，增加短语过滤规则
# version 0.3.0: 使用 lda 主题模型，同时利用 word 级别 tfidf 信息，增加短语过滤规则
# version 0.4.0: 增加依据词典，抽取特定短语抽取接口、过滤接口。
# reference: Teneva N , Cheng W . Salience Rank: Efficient Keyphrase Extraction with Topic Modeling[C]// Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers). 2017.

# setup
setup(name="ckpe",
      version="0.4.0",
      url="https://github.com/dongrixinyu/chinese_keyphrase_extractor",
      author="dongrixinyu",
      author_email="dongrixinyu.89@163.com",
      
      py_modules=[],
      packages=[
            "ckpe",
      ],

      include_package_data=True,
      install_requires=[
          "pkuseg"
      ],

      entry_points={
      },
)
