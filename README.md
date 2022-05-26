# chinese_keyphrase_extractor (CKPE)

一个从 **中文自然语言文本**  中抽取 **关键短语** 的工具，只消耗 **35M** 内存   
A tool for automatic **keyphrase extraction** from **Chinese** text.

### ⭐[CKPE在线版](http://182.92.160.94:16666/#/extract_keyphrase)，可以直接进入试用关键短语抽取功能。
### 本项目已经**ALREADY**迁移至 [JioNLP](https://github.com/dongrixinyu/JioNLP) 工具包，性能更好，速度更快哦~~~
### 当前工具语料最新时间为 2020年6月。此后的出现的新词不容易识别，须根据新语料处理。
## 应用场景 Application scenario

#### 1.抽取关键短语

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

- 我们往往需要更细化的短语描述，来作为文本的关键信息展示。这样的需求在生成词云、提供摘要阅读、关键信息检索等任务中都非常重要。   
- We often need more detailed phrase descriptions to display the key information of the text. Such requirements, namely keyphrases extraction, are very important in generating word cloud, providing abstract reading, key information retrieval and other tasks.  
例如：
For example:  
```
>>> phrases = ['俄罗斯克里姆林宫', '邀请金正恩访俄', '最高司令官金正恩', 
               '朝方转交普京', '举行会谈']
```

#### 2.扩展相关短语词汇

- 有时产品和客户给定了一些词汇列表，比如化工经营业务词汇“聚氯乙烯”、“塑料”、“切割”、“金刚石”等。想要找到跟这些词汇相关的短语。
- 在做**NER命名实体识别任务**的时候，我们需要从文本中，将已有的类型词汇做扩充，如“机构”类别，但我们仅知道机构的一些特征，如常以“局”、“法院”、“办公室”等特征词结尾。
- 在下面的使用样例中，给出了上述两种需求的扩展短语识别的方法。

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
git clone https://github.com/dongrixinyu/chinese_keyphrase_extractor
cd ./chinese_keyphrase_extractor
pip install .
```

- [JioNLP](https://github.com/dongrixinyu/JioNLP) 同样支持短语抽取，工具包安装方法：
```
$ pip install jionlp
```


#### 示例代码 Sample code 

- 输入必须为 **utf-8** 编码字符串  
- 具体函数参数见代码  
- Input must be **utf-8** encoding string  
- Check code for specific function parameters  

##### 1.抽取关键短语
```
import ckpe    

ckpe_obj = ckpe.ckpe()
# 初次导入时会自动下载北大词性标注模型包，自动加载入内存（50M）  
# 若由于网速原因下载失败，请参考 https://github.com/lancopku/pkuseg-python 如何安装下载 pkuseg 默认模型  
# Speech Tagging Model Package of pkyseg will be downloaded automatically upon initial import  
# If downloading fails due to network speed, please refer to how to install and download pkuseg default model in https://github.com/lancopku/pkuseg-python  

text = '法国媒体最新披露，巴黎圣母院火灾当晚，第一次消防警报响起时，负责查验的保安找错了位置，因而可能贻误了救火的最佳时机。...'
key_phrases = ckpe_obj.extract_keyphrase(text)
print(key_phrases)
print(ckpe_obj.extract_keyphrase.__doc__)
```

- **JioNLP 工具包调用方法**：
```
>>> import jionlp as jio
>>> text = '朝鲜确认金正恩出访俄罗斯 将与普京举行会谈...'
>>> key_phrases = jio.keyphrase.extract_keyphrase(text)
>>> print(key_phrases)
>>> print(jio.keyphrase.extract_keyphrase.__doc__)

# ['俄罗斯克里姆林宫', '邀请金正恩访俄', '举行会谈',
#  '朝方转交普京', '最高司令官金正恩']
```


##### 2.扩展类型短语
```
text = '聚氯乙烯树脂、塑料制品、切割工具、人造革、人造金刚石、农药（不含危险化学品）、针纺织品自产自销。...'
word_dict = {'聚氯乙烯': 1, '塑料': 1, '切割': 1, '金刚石': 1}  # 词汇: 词频（词频若未知可全设 1）
key_phrases = ckpe_obj.extract_keyphrase(text, top_k=-1, specified_words=word_dict)
print(key_phrases)
```

##### 3.NER任务的短语扩充
```
text = '国务院下发通知，山西省法院、陕西省检察院、四川省法院、成都市教育局。...'
word_dict = {'局': 1, '国务院': 1, '检察院': 1, '法院': 1}
key_phrases = ckpe_obj.extract_keyphrase(text, top_k=-1, specified_words=word_dict, 
                                         remove_phrases_list=['麻将局'])
print(key_phrases)
```

#### [关键短语抽取技术总结](https://github.com/dongrixinyu/chinese_keyphrase_extractor/wiki/%E5%85%B3%E9%94%AE%E7%9F%AD%E8%AF%AD%E6%8A%BD%E5%8F%96%E6%8A%80%E6%9C%AF%E7%AE%80%E8%BF%B0)
#### [关于如何自己根据特定语料训练模型，各个文件的计算方法说明](https://github.com/dongrixinyu/chinese_keyphrase_extractor/wiki/%E5%90%84%E4%B8%AA%E7%BB%9F%E8%AE%A1%E6%96%87%E4%BB%B6%E7%9A%84%E8%AE%A1%E7%AE%97%E6%96%B9%E6%B3%95)

#### 计算主题向量

- 工具包中默认的主题模型参数由100万篇各个类型的新闻文本，以及少部分社交媒体文本训练得到。
- 若需要针对特定领域文本处理，则需要根据特定的语料重新训练模型，并按相应的文件格式做替换。
- 主题模型采用标准的 LDA 模型训练得到，工具包可选择 gensim、sklearn、familia 等，训练完毕后可以得到主题词的分布表示，进而可以得到每个词汇在不同主题下的分布。由此可以得出词汇的主题突出度。

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
    - 短语重复度计算 MMR 添加其中  
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

## TODO
- pkuseg 分词器造成的错误，如把时间识别为名词，数字识别为人名等
- stopwords 表中一些词汇既可以做实词，又可以做虚词，如“本”，“类”，造成错误
- 规则过滤不完善造成的错误，或过滤过强造成的漏选

## Reference  
- Teneva N , Cheng W . Salience Rank: Efficient Keyphrase Extraction with Topic Modeling[C]// Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers). 2017.  
- Liu Z , Huang W , Zheng Y , et al. Automatic Keyphrase Extraction via Topic Decomposition[C]// Proceedings of the 2010 Conference on Empirical Methods in Natural Language Processing, EMNLP 2010, 9-11 October 2010, MIT Stata Center, Massachusetts, USA, A meeting of SIGDAT, a Special Interest Group of the ACL. Association for Computational Linguistics, 2010.

## 我的窝 My blog  

如果觉得方便好用，可以请我喝杯咖啡 (●'◡'●)  

![image](../../blob/master/payment_code.jpg)




