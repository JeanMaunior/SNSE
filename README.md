





# SNSE - Sina News Search Engine

# 新浪新闻搜索引擎



[TOC]























### 1.系统框架

- 爬虫：Scrapy
- 数据库：MySQL
- 搜索引擎框架：Whoosh   (使用ieba 中文分词)
- web框架：Django

![img](.\IMG\System Framework.jpg)



### 2. 系统模块设计

#### 2.1 Scrapy爬虫

##### 2.1.1 Scrapy项目文件架构

- SNSpider
  - spider
    - snsppider.py        爬虫设计文件
  - item.py                      爬虫字段定义
  - middlewares.py      中间件
  - pipelines.py             管道文件，存取数据
  - setting.py                 爬虫设置
  - run_spider.py          爬虫运行命令
- pause                断点存取文件夹
- scrapy.cfy         配置信息文件



##### 2.1.2 爬取网站

爬取新浪新闻网站 https://news.sina.com.cn/ 下的新闻页面

通过url格式限制爬取内容的页面

根据网页的超链接建立爬虫网络。用广度优先搜索策略进行搜索

采用随机User-Agent，爬取延时设置3秒，减少反爬限制

##### 2.1.3 爬虫字段

| 字段名          | 类型    | 含义         |
| --------------- | ------- | ------------ |
| newsTitle       | striing | 新闻标题     |
| newsUrl         | striing | 新闻页面url  |
| newsAuthor      | striing | 新闻来源     |
| newsPublishTime | striing | 新闻发布日期 |
| newsContent     | striing | 新闻内容     |

##### 2.1.4 存取方式：

- MySQL同步/异步存储
- JSON文件存储

最终使用的MySQL存取数据，方便建立索引时读出



#### 2.2 MySQL数据库

##### 2.2.1 数据库基本配置

数据库名：sina

数据表名：pages

更改相应信息应同步修改scrapy与whoosh链接数据库的设置

##### 2.2.2 数据表字段

| 字段名          | 类型    |      | 含义                 |
| --------------- | ------- | ---- | -------------------- |
| newsTitle       | varchar | 35   | 新闻标题             |
| newsUrl         | varchar | 100  | 新闻页面url          |
| newsUrlMd5      | varchar | 32   | url的MD5编码         |
| newsAuthor      | varchar | 10   | 新闻来源             |
| newsPublishTime | varchar | 20   | 新闻发布日期         |
| newsContent     | varchar | 5000 | 新闻内容             |
| indexed         | varchar | 5    | 该条数据是否建立索引 |



#### 2.3 Whoosh搜索框架 与 jieba中文分词

##### 2.3.1 jieba分词

whoosh对中文分词的效果较差，从jieba.analyse导入ChineseAnalyzer中文分析器

##### 2.3.2 whoosh索引schema

| Field Name      | Field | stored | analyzer        |
| --------------- | ----- | ------ | --------------- |
| newsTitle       | TEXT  | True   | ChineseAnalyzer |
| newsUrl         | ID    | True   |                 |
| newsAuthor      | TEXT  | True   | ChineseAnalyzer |
| newsPublishTime | TEXT  | True   |                 |
| newsContent     | TEXT  | True   | ChineseAnalyzer |

[^stored]: 是否存取到磁盘，影响存取空间和建立索引时间，但搜索结果可直接从索引中取出
[^Field.ID]: 以newsUrl作为新闻的唯一标识

确定schema后读取文件信息建立索引 whoosh_index

##### 2.3.3 whoosh搜索query

搜索域：newsTitle、newsContent、newsAuthor、newsUrl

限定返回结果数量：20	（只对返回结果计算score，影响执行速度）

关键词组合逻辑：query关键词采用OR逻辑，重要度为0.5

score计算方法：BM25F （default），加入newsPublishTime为结果排序因素



#### 2.4 Django框架搭建web搜索页面

##### 2.4.1 Django项目文件架构

- SNsearcher         项目文件夹
  - settings.py        项目配置文件
  - urls.py                url逻辑
  - view.py               视图渲染
  - wsgi.py                wsgi配置
- templates             html页面模板文件夹
  - main.html           搜索主页面（base模板）
  - result.html          搜索结果页面
- mange.py             django配置命令
- run_server.py      django服务启动命令

##### 2.4.2 搜索结果

搜索请求：通过搜索框GET请求获取查询query，从建立的倒排索引获取搜索结果

结果显示：新闻标题、发布日期、新闻来源、新闻部分内容，可点击页面跳转到新闻原网页；展示top20的页面

结果统计：统计搜索匹配的总文档数和搜索执行时间（页面反馈时间和网络下载速度不计入）

关键词高亮：对搜索结果的新闻标题和新闻内容出现的查询关键词高亮



![main](.\IMG\main.png)

![search](.\IMG\search.png)



### 3. 评估

#### 3.1 评估报告

见同目录 evaluate.doc

#### 3.2 精度

For ranking list:      (Mean Average Precison) MAP = 0.914861

For non-rankinig list:      Average Precision = 0.820000

#### 3.3 响应时间

Mean Response Time = 0.087994