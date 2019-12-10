# chinese_keyphrase_extractor

一个从 **中文自然语言文本**  中抽取 **关键短语** 的工具  
A tool for **keyphrase extraction automatically** from **chinese natural language** text.

## 应用场景 Application scenario

- 在很多关键词提取任务中，使用tfidf、textrank等方法提取得到的仅仅是若干零碎词汇。  
- 这样的零碎词汇无法真正的表达文章的原本含义，我们并不想要它。  
- In many keyword extraction tasks, only a few fragmentary words are extracted when using tfidf, textrank and other methods.
- Such fragmentary words cannot really express the original meaning of the article. We do not want it.  
例如：  
For example:  
```
>>> text = '朝鲜确认金正恩出访俄罗斯 将与普京举行会谈...'
>>> keywords = ['俄罗斯', '朝鲜', '普京', '金正恩', '俄方']
```

- 在很多时候，我们往往需要更细化的短语描述，来作为文本的关键信息展示。这样的需求在生成词云、提供摘要阅读、关键信息检索等任务中都非常重要。   
- In many cases, we often need more detailed phrase descriptions to display the key information of the text. Such requirements, namely keyphrases extraction, are very important in generating word cloud, providing abstract reading, key information retrieval and other tasks.  
例如：  
For example:  
```
>>> phrases = ['俄罗斯克里姆林宫', '邀请金正恩访俄', '最高司令官金正恩', 
               '朝方转交普京', '举行会谈']
```

## 功能介绍 Function introduction

为解决以上问题，基于北大分词器 pkuseg 工具，开发了一个关键短语抽取器，它可以方便地从文本中找出表达完成意思的关键短语。  
In order to solve the above problem, I developed a keyphrase extractor based on pkuseg segmentation tool, which can easily find out the keyphrases expressing the complete meaning from the text.  

## 使用方法 Usage

#### 安装 Installation
- 仅支持 python3  
- 自动安装 pkuseg 依赖包   
- python3 only supported  
- Automatic installation of pkuseg dependency package  


```
$ git clone https://github.com/dongrixinyu/chinese_keyphrase_extractor
$ cd ~/chinese_keyphrase_extractor
$ pip install .
```


#### 示例代码 Sample code 

- 输入必须为 **utf-8** 编码字符串  
- 具体函数参数见代码  
- Input must be **utf-8** encoding string  
- See code for specific function parameters  


```
import ckpe    
# 初次导入时会自动下载北大词性标注模型包  
# 若由于网速原因下载失败，请参考 https://github.com/lancopku/pkuseg-python 如何安装下载 pkuseg 默认模型  
# Speech Tagging Model Package of pkyseg will be downloaded automatically upon initial import  
# If downloading fails due to network speed, please refer to how to install and download pkuseg default model in https://github.com/lancopku/pkuseg-python  

text = '法国媒体最新披露，巴黎圣母院火灾当晚，第一次消防警报响起时，负责查验的保安找错了位置，因而可能贻误了救火的最佳时机。...'
key_phrases = ckpe.extract(text)
print(key_phrases)
```

## 新版 3.0 New Version 3.0
- 从 jieba 分词器迁移到 pkuseg，因为 jieba 分词器过于粗放  
- 新增了停用词规则、虚词规则等  
- 新增了 LDA 主题模型权重  
- Migrate from jieba segmenter to pkuseg because jieba segmenter is too extensive.  
- Stop words rule and function word rule have been added  
- Added LDA Topic Model Weight  

## 原理 Principle of algorithm

- 首先基于 pkuseg 工具做分词和词性标注，再使用 tfidf 计算文本的关键词权重，  
- 关键词提取算法找出碎片化的关键词，然后再根据相邻关键碎片词进行融合，重新计算权重，去除相似词汇。得到的融合的多个关键碎片即为关键短语。  
    - 短语的 token 长度不超过 12  
    - 短语中不可出现超过1个虚词  
    - 短语的两端 token 不可是虚词和停用词  
    - 短语中停用词数量不可以超过规定个数  
    - 短语重复度计算添加其中  
    - 提供仅抽取名词短语功能  
- 使用预训练好的 LDA 模型，计算文本的主题概率分布，以及每一个候选短语的主题概率分布，得到最终权重  
- Firstly do word segmentation and part of speech tagging based on pkuseg tool, then use word level tfidf to calculate the keyword weight of the text.  
- Fuse the adjacent key fragment words, recalculates the weights, and removes the similar words. The fused key fragments are candidate keyphrases. Rules include:  
    - Token length of phrase can not exceed 20  
    - There cannot be more than one function word in a phrase  
    - The token at both ends of the phrase should not be the function word and stop words  
    - The number of stopwords in a phrase cannot exceed the specified number  
    - Phrase repetition calculation is added  
    - Provide only noun phrases extraction parameters  
- Calculating the topic probability distribution of the text and the topic probability distribution of each candidate phrase by using the pre-trained LDA model to obtain the final weight  

## Reference  
- reference: Teneva N , Cheng W . Salience Rank: Efficient Keyphrase Extraction with Topic Modeling[C]// Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers). 2017.  

## 我的窝 My blog  

如果觉得方便好用，请 follow 我一波：https://github.com/dongrixinyu  
If you feel this tool convenient and easy to use, please follow me: https://github.com/dongrixinyu


