# -*- encoding=utf-8 -*-
# ------------------------------------
# Create On 2019/04/26 10:20 
# File Name: keywords_extractor.py
# Edit Author: dongrixinyu
# ------------------------------------

from os.path import join, dirname, basename
import re
import pdb
import json
import pkuseg


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
    原理简述：在tfidf方法提取的碎片化的关键词（默认使用pkuseg的分词工具）基础上，
    将在文本中相邻的关键词合并，并根据权重进行调整，同时合并较为相似的短语，
    组合成结果进行返回。
    
    使用方法为：
    >>> import phrases_extractor as pe
    >>> phrases = pe.extract(text)
    
    """
    def __init__(self, ):
        
        # 词性参考 https://github.com/lancopku/pkuseg-python/blob/master/tags.txt
        self.pos_name = ['n', 't', 's', 'f', 'm', 'q', 'b', 'r', 'v', 'a', 'z',
                         'd', 'p', 'c', 'u', 'i', 'l', 'j', 'h', 'k', 
                         'g', 'x', 'nr', 'ns', 'nt', 'nx', 'nz', 'vd', 'vx', 'ad', 'an']
        self.pos_exception = ['u', 'p', 'c', 'y', 'e', 'o']
        self.redundent_pattern = re.compile(
            r'[\d+|\.|\*|\(|\)|\n|\t|\r|\{|\}|\[|\]|\,|\-|\?|\!|\%|\/|\+|。|，|\;|\'|\"|？|！|；]')
        
        fine_punctuation='[，。;；…！、：!?？\r\n ]'
        self.puncs_fine_ptn = re.compile(fine_punctuation)
        self.idf_file_path = join(dirname(__file__), "idf.txt")
        self._load_idf()
        self.seg = pkuseg.pkuseg(postag=True)  # 北大分词器
        
        # 权重字典，调整绝大多数的短语要位于2~6个词之间
        self.phrases_length_control_dict = {1: 1, 2: 5.6, 3:1.1, 4:2.0, 5:0.7, 6:0.9, 7:0.48,
                                            8: 0.43, 9: 0.24, 10:0.15, 11:0.07, 12:0.03, 13:0.01}
        self.phrases_length_control_none = 0.01  # 在大于 7 时选取
        
        # 读取停用词文件
        with open(join(dirname(__file__), "stop_word.txt"), 'r', encoding='utf8') as f:
            self.stop_words = list(set(f.read().split()))
            if '' in self.stop_words:
                self.stop_words.remove('')
            if '' not in self.stop_words:
                self.stop_words.append('\n')
    
    def _filter_stopwords(self, vocabulary):
        return [(word, weight) for word, weight in vocabulary if word not in self.stop_words]

    def _load_idf(self):
        with open(self.idf_file_path, 'r', encoding='utf-8') as f:
            idf_list = [line.strip().split(' ') for line in f.readlines()]
        self.idf_dict = dict()
        for item in idf_list:
            self.idf_dict.update({item[0]: float(item[1])})
        self.median_idf = sorted(self.idf_dict.values())[len(self.idf_dict) // 2]
    
    def _split_sentences(self, text):
        """ 将文本切分为若干句子 """
        tmp_list = self.puncs_fine_ptn.split(text)
        sentences = [sen for sen in tmp_list if sen != '']
        return sentences
    
    def extract_phrases(self, text, top_k=5, with_weight=False,
                        func_word_num=1, stop_word_num=0):
        """
        抽取一篇文本的关键短语
        :param text: utf-8 编码中文文本
        :param top_k: 选取多少个关键短语返回
        :param with_weight: 指定返回关键短语是否需要权重
        :param func_word_num: 允许短语中出现的虚词个数
        :param stop_word_num: 允许短语中出现的停用词个数
        :return: 关键短语及其权重
        """ 
        # step1: 分句，使用北大的分词器 pkuseg 做分词和词性标注
        sentences_list = self._split_sentences(text)
        sentences_segs_list = list()
        counter_segs_list = list()
        for sen in sentences_list:
            
            sen_segs = self.seg.cut(sen)
            sentences_segs_list.append(sen_segs)
            counter_segs_list.extend(sen_segs)
            
        # step2: 计算词频
        total_length = len(counter_segs_list)
        freq_dict = dict()
        for word_pos in counter_segs_list:
            word, pos = word_pos
            if word in freq_dict:
                freq_dict[word][1] += 1
            else:
                freq_dict.update({word: [pos, 1]})
        
        # step3: 计算每一个词的权重
        sentences_segs_weights_list = list()
        for sen, sen_segs in zip(sentences_list, sentences_segs_list):
            sen_segs_weights = list()
            for word_pos in sen_segs:
                word, pos = word_pos
                if pos in self.pos_name:  # 虚词权重为 0
                    if word in self.stop_words:  # 停用词权重为 0
                        weight = 0.0
                    else:
                        weight = freq_dict[word][1] * self.idf_dict.get(word, self.median_idf) / total_length
                else:
                    weight = 0.0
                sen_segs_weights.append(weight)
            sentences_segs_weights_list.append(sen_segs_weights)
                
        #print(sentences_segs_list[0])
        #print(sentences_segs_weights_list[0])
        #print(len(sentences_segs_list))
        #print(len(sentences_segs_weights_list))
        
        # step4: 通过一定规则，找到候选短语集合，以及其权重
        candidate_phrases_dict = dict()
        for sen_segs, sen_segs_weights in zip(sentences_segs_list, sentences_segs_weights_list):
            sen_length = len(sen_segs)
            
            for n in range(1, sen_length + 1):  # n-grams
                for i in range(0, sen_length - n + 1):
                    candidate_phrase = sen_segs[i: i + n]
                    
                    # 找短语过程中需要进行过滤
                    # 条件一：一个短语不能超过20个 token
                    if len(candidate_phrase) > 20:
                        continue
                    
                    # 条件一：一个短语中不能出现超过一个虚词
                    more_than_one_func_word_count = 0
                    for item in candidate_phrase:
                        if item[1] in self.pos_exception:
                            more_than_one_func_word_count += 1
                    if more_than_one_func_word_count > func_word_num:
                        continue
                    
                    # 条件二：短语的前后不可以是虚词、停用词，短语末尾不可是动词
                    if candidate_phrase[0][1] in self.pos_exception or candidate_phrase[len(candidate_phrase)-1][1] in self.pos_exception:
                        continue
                    if candidate_phrase[len(candidate_phrase)-1][1] in ['v', 'd']:
                        continue
                    if candidate_phrase[0][0] in self.stop_words or candidate_phrase[len(candidate_phrase)-1][0] in self.stop_words:
                        continue
                        
                    # 条件三：短语中不可以超过规定个数的停用词
                    has_stop_words_count = 0
                    for item in candidate_phrase:
                        if item[0] in self.stop_words:
                            has_stop_words_count += 1
                    if has_stop_words_count > stop_word_num:
                        continue
                        #pdb.set_trace()
                        
                    length_weight = self.phrases_length_control_dict.get(len(sen_segs_weights[i: i + n]), self.phrases_length_control_none)
                    candidate_phrase_weight = sum(sen_segs_weights[i: i + n]) * length_weight
                    #print(candidate_phrase_weight, candidate_phrase)
                    #print(sen_segs_weights[i: i + n])
                    candidate_phrase_string = ''.join([tup[0] for tup in candidate_phrase])
                    if candidate_phrase_string not in candidate_phrases_dict:

                        candidate_phrases_dict.update({candidate_phrase_string: [candidate_phrase, candidate_phrase_weight]})
            #pdb.set_trace()
        #print(type(candidate_phrases_dict))
        
        # step5: 将 overlaping 过量的短语进行去重过滤
        candidate_phrases_list = sorted(candidate_phrases_dict.items(), key=lambda item: len(item[1][0]), reverse=True)
        de_duplication_candidate_phrases_list = list([candidate_phrases_list[0]])
        #print(de_duplication_candidate_phrases_list)
        
        for item in candidate_phrases_list[1:]:
            no_duplication_flag = False
            for de_du_item in de_duplication_candidate_phrases_list:
                common_num = len(set(item[1][0]) & set(de_du_item[1][0]))
                #print(item[1][0])
                #print(de_du_item[1][0])
                #print(common_num, '--', len(set(item[1][0])), len(set(de_du_item[1][0])))
                #pdb.set_trace()
                if common_num >= min(len(set(item[1][0])), len(set(de_du_item[1][0])))/2.0:
                    # 这里影响了短语的长度，造成 4 token 组成的短语数量太少
                    # 重复度较高的短语进行过滤，不再进入候选序列中
                    no_duplication_flag = True
                    break
            if not no_duplication_flag:
                de_duplication_candidate_phrases_list.append(item)
                
        # step6: 按重要程度进行排序，选取 top_k 个
        candidate_phrases_list = sorted(de_duplication_candidate_phrases_list, key=lambda item: item[1][1], reverse=True)
        
        for idx, item in enumerate(candidate_phrases_list):
            if idx < top_k:
                #print(item[1][1], item[0])
                #print(item[1][0])
                
                pass
        
        if with_weight:
            final_res = [(item[0], item[1][1]) for item in candidate_phrases_list[:top_k]]
        else:
            final_res = [item[0] for item in candidate_phrases_list[:top_k]]
            
        return final_res


if __name__ == '__main__':
    title = '巴黎圣母院大火：保安查验火警失误 现场找到7根烟头'
    text = '法国媒体最新披露，巴黎圣母院火灾当晚，第一次消防警报响起时，负责查验的保安找错了位置，因而可能贻误了救火的最佳时机。据法国BFMTV电视台报道，4月15日晚，巴黎圣母院起火之初，教堂内的烟雾报警器两次示警。当晚18时20分，值班人员响应警报前往电脑指示地点查看，但没有发现火情。20分钟后，警报再次响起，保安赶到教堂顶部确认起火。然而为时已晚，火势已迅速蔓延开来。报道援引火因调查知情者的话说，18时20分首次报警时，监控系统侦测到的失火位置准确无误。当时没有发生电脑故障，而是负责现场查验的工作人员走错了地方，因而属于人为失误。报道称，究竟是人机沟通出错，还是电脑系统指示有误，亦或是工作人员对机器提示理解不当？事发当时的具体情形尚待调查确认，以厘清责任归属。该台还证实了此前法媒的另一项爆料：调查人员在巴黎圣母院顶部施工工地上找到了7个烟头，但并未得出乱扔烟头引发火灾的结论。截至目前，警方尚未排除其它可能性。大火发生当天（15日）晚上，巴黎检察机关便以“因火灾导致过失损毁”为由展开司法调查。目前，巴黎司法警察共抽调50名警力参与调查工作。参与圣母院顶部翻修施工的工人、施工方企业负责人以及圣母院保安等30余人相继接受警方问话。此前，巴黎市共和国检察官海伊茨曾表示，目前情况下，并无任何针对故意纵火行为的调查，因此优先考虑的调查方向是意外失火。调查将是一个“漫长而复杂”的过程。现阶段，调查人员尚未排除任何追溯火源的线索。因此，烟头、短路、喷焊等一切可能引发火灾的因素都有待核实，尤其是圣母院顶部的电路布线情况将成为调查的对象。负责巴黎圣母院顶部翻修工程的施工企业负责人在接受法国电视一台新闻频道采访时表示，该公司部分员工向警方承认曾在脚手架上抽烟，此举违反了工地禁烟的规定。他对此感到遗憾，但同时否认工人吸烟与火灾存在任何直接关联。该企业负责人此前还曾在新闻发布会上否认检方关于起火时尚有工人在场的说法。他声称，火灾发生前所有在现场施工的工人都已经按点下班，因此事发时无人在场。《鸭鸣报》在其报道中称，警方还将调查教堂电梯、电子钟或霓虹灯短路的可能性。但由于教堂内的供电系统在大火中遭严重破坏，有些电路配件已成灰烬，几乎丧失了分析价值。此外，目前尚难以判定究竟是短路引发大火还是火灾造成短路。25日，即巴黎圣母院发生震惊全球的严重火灾10天后，法国司法警察刑事鉴定专家进入失火现场展开勘查取证工作，标志着火因调查的技术程序正式启动。此前，由于灾后建筑结构仍不稳定和现场积水过多，调查人员一直没有真正开始采集取样。'
    jieba_tfidf = [('调查', 0.23225761698485342), ('火灾', 0.22277054119869708), ('巴黎圣母院', 0.17397071379641693), ('短路', 0.1330527452495114), ('圣母院', 0.12510161592801303)]
    
    pe = PhrasesExtractor()
    key_phrases = pe.extract_phrases(text)
    print('key_phrases: ', key_phrases)
    print('jieba_tfidf: ', jieba_tfidf)

