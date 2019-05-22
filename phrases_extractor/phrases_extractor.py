# -*- encoding=utf-8 -*-
# ------------------------------------
# Create On 2019/04/26 10:20 
# File Name: keywords_extractor.py
# Edit Author: dongrixinyu
# ------------------------------------

from os.path import join, dirname, basename
import re
import json
import jieba
import jieba.analyse


class PhrasesExtractor(object):
    """
    该类解决如下问题：
    在很多关键词提取任务中，使用tfidf方法提取得到的仅仅是若干零碎词汇。
    这样的零碎词汇无法真正的表达文章的原本含义。
    e.g. 
    >>> text = '朝鲜确认金正恩出访俄罗斯 将与普京举行会谈...'
    >>> keywords = ['俄罗斯', '朝鲜', '普京', '金正恩', '俄方']
    
    在生成词云、提供摘要阅读、关键信息检索等任务中，往往需要更细化的短语描述，
    来作为文本的关键词。
    e.g.
    >>> phrases = ['俄罗斯克里姆林宫', '邀请金正恩访俄', '最高司令官金正恩', 
                   '朝方转交普京', '举行会谈']
    
    该类即可在tfidf方法提取的碎片化的关键词基础上，进而得到短语化的关键词。
    原理简述：在tfidf方法提取的碎片化的关键词（默认使用jieba的）基础上，
    将在文本中相邻的关键词合并，并根据权重进行调整，同时合并较为相似的短语，
    组合成结果进行返回。
    
    使用方法为：
    >>> import phrases_extractor as pe
    >>> phrases = pe.extract(text)
    
    """
    def __init__(self):
        self.pos_name = ['a', 'ad', 'an', 'd', 'ns', 'n', 'nt', 'nz', 'vn', 'v', 'nr']
        self.redundent_pattern = re.compile(
            r'[\d+|\.|\*|\(|\)|\n|\t|\r|\{|\}|\[|\]|\,|\-|\?|\!|\%|\/|\+|。|，|\;|\'|\"|？|！|；]')
        with open(join(dirname(__file__), "stop_word.txt"), 'r', encoding='utf8') as f:
            self.stop_words = set(f.read().split())
    
    def _filter_stopwords(self, vocabulary):
        return [(word, weight) for word, weight in vocabulary if word not in self.stop_words]

    def extract_phrases(self, text, keywords_res=None, top_k=5, with_weight=True,
                        allow_pos=(), top_k_features=50):
        """
        抽取一篇文本的关键短语
        :param text: utf-8 编码中文文本
        :param keywords_res: 若不想用 jieba 默认工具，则须指定如下格式的碎片话关键词。
            其数量一般需要和 top_k_features 保持相同数量级
             e.g. [('调查', 0.23), ('火灾', 0.22), ('巴黎圣母院', 0.17), 
			       ('短路', 0.13), ('圣母院', 0.12), ...]
        :param top_k: 选取多少个关键短语返回
        :param with_weight: 指定返回关键短语是否需要权重
        :param allow_pos: 指定哪些词性类型的关键词碎片进行，默认指定了一些实词
		:param top_k_features: 参与关键短语合并的关键碎片数量，默认50个
        :return: 关键短语及其权重
        """ 
        # jieba 的 tfidf 算法
        if keywords_res is None:
            if allow_pos:
                keywords_res = jieba.analyse.extract_tags(
                    text, topK=top_k_features, withWeight=True, allowPOS=allow_pos)
            else:
                keywords_res = jieba.analyse.extract_tags(
                    text, topK=top_k_features, withWeight=True, allowPOS=self.pos_name)
        
        key_phrases = self._key_phrase(text, keywords_res, top_k=top_k)
        if with_weight:
            return key_phrases
        else:
            return [item[0] for item in key_phrases]
        
    def _cut_sentences(self, text):
        """对文本进行分句，并对句子进行分词"""
        cut_sentences = []
        sentences = re.findall(u".*?[。？！]", text)
        for sentence in sentences:
            cut_sentences.append(jieba.lcut(sentence))
        return cut_sentences
        
    def _key_phrase(self, text, keywords_weight, top_k=5):
        """提取关键短语
        """
        keywords_score = {item[0]: item[1] for item in keywords_weight}
        cut_sentences = self._cut_sentences(text)
        keywords = keywords_score.keys()

        # 从文本中筛选出相邻的关键词组成短语
        key_phrase = []
        for cut_sent in cut_sentences:
            temp = []
            for word in cut_sent:
                if word in keywords:
                    temp.append(word)
                else:
                    if len(temp) > 1:
                        if temp not in key_phrase:
                            key_phrase.append(temp)
                    if len(temp) == 0:
                        continue
                    else:
                        temp = []

        # 提取出的短语可能存在冗余现象，这里对冗余短语进行过滤
        key_phrase_filter = []
        for item1 in key_phrase:
            # 由于短语可能包含的关键词很多，导致最后输出很长，这里仅保留相邻关键词的后三个
            item1 = item1[-3:]
            flag = False
            for item2 in key_phrase_filter:
                # 对冗余进行过滤
                if len(set(item1) & set(item2)) >= min(len(set(item1)), len(set(item2)))/2.0:
                    flag = True
                    break
            if not flag:
                key_phrase_filter.append(item1)

        # 取短语中包含的关键词的权重的均值作为短语权重
        key_phrase_filter_score = []
        for item in key_phrase_filter:
            phrase = ''
            score = []
            for word in item:
                phrase += word
                score.append(keywords_score[word])
            key_phrase_filter_score.append((phrase, sum(score)/len(score)))

        # 合并关键短语和关键词,如果关键词出现在短语中，排除
        key_phrase_filter_str = '|'.join([word for word, score in key_phrase_filter_score])
        merged_phrase_word = key_phrase_filter_score[:]
        for word1, score1 in keywords_score.items():
            if word1 not in key_phrase_filter_str:
                merged_phrase_word.append((word1, score1))
        ret_sorted = sorted(merged_phrase_word, key=lambda x: x[1], reverse=True)
        return ret_sorted[:top_k]

        
if __name__ == '__main__':
    title = '巴黎圣母院大火：保安查验火警失误 现场找到7根烟头'
    text = '法国媒体最新披露，巴黎圣母院火灾当晚，第一次消防警报响起时，负责查验的保安找错了位置，因而可能贻误了救火的最佳时机。据法国BFMTV电视台报道，4月15日晚，巴黎圣母院起火之初，教堂内的烟雾报警器两次示警。当晚18时20分，值班人员响应警报前往电脑指示地点查看，但没有发现火情。20分钟后，警报再次响起，保安赶到教堂顶部确认起火。然而为时已晚，火势已迅速蔓延开来。报道援引火因调查知情者的话说，18时20分首次报警时，监控系统侦测到的失火位置准确无误。当时没有发生电脑故障，而是负责现场查验的工作人员走错了地方，因而属于人为失误。报道称，究竟是人机沟通出错，还是电脑系统指示有误，亦或是工作人员对机器提示理解不当？事发当时的具体情形尚待调查确认，以厘清责任归属。该台还证实了此前法媒的另一项爆料：调查人员在巴黎圣母院顶部施工工地上找到了7个烟头，但并未得出乱扔烟头引发火灾的结论。截至目前，警方尚未排除其它可能性。大火发生当天（15日）晚上，巴黎检察机关便以“因火灾导致过失损毁”为由展开司法调查。目前，巴黎司法警察共抽调50名警力参与调查工作。参与圣母院顶部翻修施工的工人、施工方企业负责人以及圣母院保安等30余人相继接受警方问话。此前，巴黎市共和国检察官海伊茨曾表示，目前情况下，并无任何针对故意纵火行为的调查，因此优先考虑的调查方向是意外失火。调查将是一个“漫长而复杂”的过程。现阶段，调查人员尚未排除任何追溯火源的线索。因此，烟头、短路、喷焊等一切可能引发火灾的因素都有待核实，尤其是圣母院顶部的电路布线情况将成为调查的对象。负责巴黎圣母院顶部翻修工程的施工企业负责人在接受法国电视一台新闻频道采访时表示，该公司部分员工向警方承认曾在脚手架上抽烟，此举违反了工地禁烟的规定。他对此感到遗憾，但同时否认工人吸烟与火灾存在任何直接关联。该企业负责人此前还曾在新闻发布会上否认检方关于起火时尚有工人在场的说法。他声称，火灾发生前所有在现场施工的工人都已经按点下班，因此事发时无人在场。《鸭鸣报》在其报道中称，警方还将调查教堂电梯、电子钟或霓虹灯短路的可能性。但由于教堂内的供电系统在大火中遭严重破坏，有些电路配件已成灰烬，几乎丧失了分析价值。此外，目前尚难以判定究竟是短路引发大火还是火灾造成短路。25日，即巴黎圣母院发生震惊全球的严重火灾10天后，法国司法警察刑事鉴定专家进入失火现场展开勘查取证工作，标志着火因调查的技术程序正式启动。此前，由于灾后建筑结构仍不稳定和现场积水过多，调查人员一直没有真正开始采集取样。'
    jieba_tfidf = [('调查', 0.23225761698485342), ('火灾', 0.22277054119869708), ('巴黎圣母院', 0.17397071379641693), ('短路', 0.1330527452495114), ('圣母院', 0.12510161592801303)]
    
    pe = PhrasesExtractor()
    key_phrases = pe.extract_phrases(text)
    print('key_phrases: ', key_phrases)
    print('jieba_tfidf: ', jieba_tfidf)



    
        
