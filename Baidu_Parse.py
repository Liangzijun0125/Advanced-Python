
# coding: utf-8

# In[ ]:

'''
用以爬取 使用百度搜索 中国重名最多的名字——张伟 的搜索结果前20页正文内容并进行文本聚类；
停用词存储位置：D:\Echo\Baidu_Parse\Stopwords.txt
从网页上抓取的文件以txt格式存储，位置为：D:\Echo\Baidu_Parse\zhangwei\标题名.txt

程序流程：
1.从网页上抓取信息，生成txt文档；
2.基于抓取的信息生成语料库；
3.用jieba对结果进行切词处理；
4.去除停用词；
5.构建词袋空间;
6.将单词出现的次数转化为权值（TF-IDF）；
7.用K-means算法进行聚类.
'''

import time
import os
from os import listdir
from selenium import webdriver
import jieba
from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans

#判断页面中元素是否存在
def element_exist(css_tag):
    try:
        browser.find_element_by_tag_name(css_tag)
        return True
    except:
        return False
    
def class_para(classname):                                      #判断段落
    elems_div = browser.find_elements_by_tag_name('div')
    for elem_div in elems_div:
        if elem_div.get_attribute('class')==classname:
            return True
        else:
            return False
    return False

#程序入口
if __name__ == "__main__":
    if not os.path.exists("D:/Echo/Baidu_Parse/zhangwei"):                    #避免重复创建文件夹
        os.mkdir("D:/Echo/Baidu_Parse/zhangwei")
    browser = webdriver.Chrome()
    browser.get('https://www.baidu.com/s?wd=%E5%BC%A0%E4%BC%9F&rsv_spt=1&rsv_iqid=0xae54e34600032731&issp=1&f=8&rsv_bp=1&rsv_idx=2&ie=utf-8&rqlang=cn&tn=baiduhome_pg&rsv_enter=0&oq=%25E6%25A2%2581%25E7%25B4%25AB%25E5%2590%259B&rsv_t=a9f2pDkCepA4oQs9ifTTU7eXDKjaUFgS6yoJzjKf5nCH9jM%2FAEE87y6%2Fvhed1FYVziPv&rsv_pq=8d1f80ac0004431f&inputT=30&rsv_sug3=42&rsv_sug1=31&rsv_sug7=101&bs=%E6%A2%81%E7%B4%AB%E5%90%9B')
    
    i = 0
    while(i<20):       #抓取搜索结果前20页链接中的正文内容
        i = i + 1
        elems = browser.find_elements_by_class_name('t')
        for elem in elems:
            print("正在抓取："+elem.text)     #抓取进程可视化
            title = elem.text
            title = title.replace('?','').replace('/','').replace('<','').replace('>','').replace('|','').replace('*','').replace('"','').replace(':','')  
            #替换符号以避免文件名禁用符
            elem.find_element_by_tag_name('a').click()
            time.sleep(3)
            browser.switch_to.window(browser.window_handles[-1])          #浏览器标签页切换操作
            
            
            #分类讨论，部分页面的正文内容存放在div中的para标签中，部分直接存放于p标签中
            if class_para('para'):
                elems_div = browser.find_elements_by_class_name('para')
                for elem_div in elems_div:
                    with open('D:/Echo/Baidu_Parse/zhangwei/'+title+'.txt',"a",encoding = 'utf-8') as file:
                        #将抓取链接中的正文内容写入文档
                        file.write(elem_div.text)
                        file.write('\n')
            elif element_exist('p'):
                elems_p = browser.find_elements_by_tag_name('p')
                for elem_p in elems_p:
                    with open('D:/Echo/Baidu_Parse/zhangwei/'+title+'.txt',"a",encoding = 'utf-8') as file:
                        file.write(elem_p.text)
                        file.write('\n')
            browser.close()
            browser.switch_to.window(browser.window_handles[0])
        browser.find_elements_by_class_name('n')[-1].click()       #跳转至下一页
        time.sleep(3)
        browser.switch_to.window(browser.window_handles[0])
        
    #利用jieba分词进行中文分词，根据停用词的语料库进行停用词的过滤以及特殊字符的处理,建立语料库
    all_files = listdir('D:/Echo/Baidu_Parse/zhangwei')
    for f in all_files:
        if os.path.getsize(os.path.join('D:/Echo/Baidu_Parse/zhangwei',f)) == 0:
            os.remove(os.path.join('D:/Echo/Baidu_Parse/zhangwei',f))                      #删除结果为空的文档
    
    tags = []     #用以存储抓取内容文档名称
    corpus = []      #建立新语料库
    
    #过滤停用词
    stopwords = open('D:/Echo/Baidu_Parse/Stopwords.txt')
    texts = ['\u3000','\n',' ']                #爬取的内容中未处理的特殊字符(u3000为全角空格)
    
    #建立停用词库
    for word in stopwords:
        word = word.strip()                    #移除字符串头尾指定的字符（默认为空格或换行符）或字符序列
        texts.append(word)
        
    #建立语料库
    for i in range(0,len(all_files)):
        filename = all_files[i]
        filetag=filename.split('.')[0]
        tags.append(filetag)                    #正文内容文档名列表
        file_full = 'D:/Echo/Baidu_Parse/zhangwei/'+filename
        #print(file_full)
        doc=open(file_full,encoding='utf-8').read()
        data = jieba.cut(doc,cut_all = True)     #用jieba进行文本分词
        data_adj = ''
        delete_word = []
        for item in data:
            if item not in texts:    #停用词过滤
                data_adj+=item+' '
            else:
                delete_word.append(item)
        corpus.append(data_adj)      #语料库建立完成
    #print(corpus)
    
    #计算词语的TF-IDF值
    vectorizer=CountVectorizer()                 #将文本中的词语转换为词频矩阵，矩阵元素a[i][j] 表示j词在i类文本下的词频  
    transformer=TfidfTransformer()                  #统计每个词语的tf-idf权值
    tfidf=transformer.fit_transform(vectorizer.fit_transform(corpus))       #第一个fit_transform是计算tf-idf，第二个fit_transform是将文本转为词频矩阵
    weight=tfidf.toarray()                          #将tf-idf矩阵抽取出来，元素a[i][j]表示j词在i类文本中的tf-idf权重
    #weight为 246×9293矩阵，每一行代表一个文本，列为总次数，每一行对应的值为相关文本词语的TFIDF值
    word=vectorizer.get_feature_names()               #获取词袋模型中的所有词
    #for i in range(1,len(word)):                 #打印词袋模型中的词
        #print(word)
      
    #利用Kmeans算法实现文本聚类

    mykms=KMeans(n_clusters=10)
    y=mykms.fit_predict(weight)
    for i in range(0,10):
        tag_i=[]
        for j in range(0,len(y)):
            if y[j]==i:
                tag_i.append(tags[j])
    print('张伟_'+str(i)+':'+str(tag_i))

