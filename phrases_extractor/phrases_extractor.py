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
import jieba
import jieba.analyse
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
    原理简述：在tfidf方法提取的碎片化的关键词（默认使用jieba的）基础上，
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
        self.phrases_length_control_none = 0.01  # 在大于 13 时选取
        
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
    text = '单身经济正在崛起：商品越来越“小”生活品质更高 本报记者 赵碧报道50毫升的红酒，1人份的火锅，便利店里的2片装面包，迷你洗衣机……无论是家电、家居，还是美妆护肤、饮食快消，在不 少人的日常生活里，生活用品正在集体变“小”，这也折射出“单身经济”的正在崛起。2001年经济学家麦卡锡在《经济学人》杂志中首次提出“单身经济”。起初是为“单身女子经济”提出的概念， 认为“独身且收入不菲的单身女性是广告、娱乐等行业最理想的顾客”。如今，这个群体已不再特指“单身的女性”。目前，单身人士已经成为一个庞大的群体，尤其是在 互联网 经济中，单身经 济已经成为一个潮流。桂林理工大学公共管理与传媒学院教师刘晨在接受《中国产经新闻》记者采访时表示，在当代或未来的社会发展当中，因“量”的增大和消费升级，会带来整体性的经济发 展变化。单身经济时代“我一个人吃饭、旅行，到处走走停停；也一个人看书、写信，自己对话谈心。”这是早些年中国一首流行歌曲中的描述，而现在也是大多数单身者的现实写照。美国 社会学教授埃里克在《单身社会》一书说到：“单身社会，正成为一次空前强大、无可避免的社会变革，不少发达经济体都已经进入了这一社会形态。”从世界范围来看，“单身”已成为一种“常态”。 东兴证券 的报告显示，单身人口已占到美国成年人口的45%， 日本 为32.4%， 韩国 为23.9%，中国为14.6%。随着我国社会不断进步，微观个体选择日益多元，主动或被动选择单身的人将越来越多，比照同为东亚国家的日本和韩国，按两国的平均单身人口比例计算，未来中国的单身人口可能高达4亿。依照现有的统计数据，我国的单身人口正在成为不可忽视的一个群体。《中国统计年鉴2017》数据显示：我国20-49岁的单身人口（包括未婚和离婚的）规模已经达到2.4亿，数量已经超过了一些国家的总人口，而且数量还在增加。这些单身人群主要集中生活在北上广深等一 二线城市，其中90后占比超过60%。据媒体报道，目前中国的单身人口已经相当于 俄罗斯 和 英国 人口的总和。同时，单身人士越来越成为主流消费人群。所以，关爱“单身狗”，或者不再是一句空话。伴随消费升级，中国正迎来单身经济时代。两片装面包在便利店货架上常常断货、“一人食”指南开始越来越多地播放、迷你装红酒自动量贩机越布点越多。日常细节正在不动声色地折 射着“单身经济”正在崛起。不仅如此，在租房市场上长租式独居型公寓受到追捧，满足单身一族居住的舒适、隐私、交友等需求；在消费品上，从满足年轻消费者享受型消费、渴望便利、追逐 潮流的需求出发，注重提供中高端类型产品；为单身女性提供环境优雅、利于纤体瘦身的餐饮服务；迎合单身男女猎奇的心理，开发邮轮出海、野外生存等 旅游 产品；从国外经验看，单身人 士为爱好非常舍得买单，国内市场已有端倪。值得注意的是，单身者不仅在互联网、人工智能等技术高速发展的时代更自由和有品质地生活，享受到更多的乐趣，而且越来越多的单身族把置业 需求提上了日程，认为一个人也要“安家立业”。据58安居客房产研究院和 58同城 二手车研究院联合调研数据显示，单身人群中60.2%的受访者已经拥有自己的第一套住房，61.6%的人已经购置 一辆车。受国内传统观念影响，年轻人普遍认为买房是结婚前必不可少的环节，有62.5%的单身人士选择先买房再结婚，且新一线消费者相比一线消费者，更看重房子对婚姻的影响。中研普华研究员覃崇告诉《中国产经新闻》记者，单身社会催生和带动了单身经济的发展。单身人群比较注重生活质量，崇尚高消费生活，因此，未来市场规模巨大的单身经济更加注重个性化、品牌化等 。品质化的“小”时代与《低欲望社会》《无缘社会》中呈现的“无欲无求，孤独终老”的日本单身社会不同，中国单身群体对生活品质的追求越来越高。这种集体情绪和生活观，甚至悄然改变了 家的模样。冰箱进了卧室，洗衣机挂到了墙上，客厅不再有电视机的身影。 天猫 方面相关报告显示，180升以下的迷你冰箱在2018年购买人数增长了33.33%，据了解，这类冰箱常常放在卧室，用来冰镇小支酒、水果和面膜；专用于清洗女士内衣的壁挂式洗衣机，仅2018年6月的单月销量，就抵过了这个品牌2018年第一季度的总销量；还有迷你投影仪，2018年天猫“双11”开启预售后，超过10万人把它加入了购物车。而这些专门根据单身人群需求生产的产品，一个突出的特点就是“小”。最近两年，功能细分的迷你家电新物种不断诞生，表现最突出的是迷你语音智能音箱，销 售增长量高达160倍。此外，食物垃圾处理器、体脂称重仪、按摩椅在2018年过去9个月的销售增速分别超过160%、120%和110%。刘晨说道，食物垃圾处理器、体脂称重仪、按摩椅和180升以下的迷你冰箱的增速快，说明依附于单身社会的单身经济很可能会促进一定的经济增长，尤其是消费层次的上升与量的增大，会带来销售模式与经济发展的转变。同时，单身群体呈现出典型的“高消费、低储蓄”特点，并且注重生活品质，也让商家看到了更多的商机。有商家表示，主力人群消费观念变化将在消费升级中酝酿巨大消费潜力，比如，单身人群非常注重生活质量，更注重食品安全，对价格不敏感，追求舒适、便利的购物环境，对常规降价优惠关注度不高，但会参与会员积分促销活动。目前虽然单人餐、小型家电、微型公寓等针对单身人群的产业在迅速发展，但针对 单身族设计的针对性产品种类仍然太少，未来可能会形成越来越多的“小而美”业态。刘晨认为，单身经济的崛起对消费升级的确是有写照，或者是一种消费升级的现象。但，并不是社会学意义 上的“整体性消费升级”，而是这个群体在升级。现代社会，往往在单身群体当中，“一个人吃饱全家不饿”，而且，对商品的要求要更高档次，精细化，体积小、新鲜度高，符合单身生活特性等 ，这就导致商品也会因需要的不同而生产出不同规模与档次的产品，用以满足这个不断扩大的群体需要。天猫总监王丹认为，中国单身群体是拉动消费升级的主力大军，这个趋势将会持续很长 一段时间，“商品越来越小，功能越来越细分，是眼下我们正在经历的时代的缩影，也是消费者和大数据推动生产的生动案例。”对商家来说，可以抓住这样的一个社会群体的生活与心理需要， 生产出一些功能精细的商品以满足这部分人的需求。尤其是，单身的生活形态，比如宅，其会不会增加物流经济？会不会对产品的设计及其容易运输产生灵感？举这个例子的意思就是说，商家 不仅仅要去满足他们的档次需要，还要更加深入地分析这个群体的生活形态，要去调查和得出市场分析报告，这样就更加有利于商家的产品生产与占据市场比例，从而利润更大化，也满足了单 身群体的消费需要。覃崇说道，单身群体人口多、消费能力强，产品要求质量质量高、满足个性化，在一定程度上拉动了消费升级。而对于商家来说，“小而美”产品的巨大需求，将是下一个阶 段的风口，就看能不能成为那只高飞的猪。另外，业内认为，单身经济的红利期已到，未来将会有更多的产品服务于这一群体。覃崇表示，需求的改变必然会倒逼供给，相关生产企业必然会应 部分消费的需求而改变生产方向，这也符合供给侧的经济发展战略。同时，由于我国人口结构不会很快地发展变化，单身经济将会是未来几年甚至是十几年一个稳定的状况，相关的设施建设、 产品规划等，也在不断发展完善，“小而美”的产品成为了社会的一个需求点。（责任编辑：王治强 HF013）'    
    
    pe = PhrasesExtractor()
    key_phrases = pe.extract_phrases(text)
    print('key_phrases: ', key_phrases)



    
        
