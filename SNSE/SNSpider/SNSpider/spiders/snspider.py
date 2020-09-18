
from SNSpider.items import SnspiderItem
import scrapy
import re
import requests
import pickle
from urllib.parse import urljoin

class SNSpider(scrapy.Spider):
    # 用于区别Spider
    name = "snspider"
    # 允许访问的域
    allowed_domains = ['sina.com.cn']
    # 爬取的起始地址
    start_urls = ['https://news.sina.com.cn/']
    # start_urls = ['https://news.sina.com.cn/s/2020-08-04/doc-iivhvpwx9157206.shtml']
    # 限制爬取的网页
    base_url = 'https://news.sina.com.cn/'
    suffixes = ['c/', 'w/', 'sf/', 's/', 'o/']
    # 将要爬取的地址列表
    destination_list = start_urls
    # 已爬取地址md5集合
    url_md5_seen = []
    # 断点续爬计数器
    counter = 0
    # 保存频率，每多少次爬取保存一次断点
    save_frequency = 50

    # 重写init
    def __init__(self):
        super
        # 读取已保存的断点
        import os
        if not os.path.exists('./pause/'):
            os.mkdir('./pause/')
        if not os.path.isfile('./pause/response.seen'):
            f = open('./pause/response.seen', 'wb')
            f.close()
        if not os.path.isfile('./pause/response.dest'):
            f = open('./pause/response.dest', 'wb')
            f.close()

        f = open('./pause/response.seen', 'rb')
        if os.path.getsize('./pause/response.seen') > 0:
            self.url_md5_seen = pickle.load(f)
        f.close()
        f = open('./pause/response.dest', 'rb')
        if os.path.getsize('./pause/response.dest') > 0:
            self.start_urls = pickle.load(f)
            self.destination_list = self.start_urls
        f.close()

        self.counter += 1


    # 爬取方法
    def parse(self, response):

        # 断点续爬功能之保存断点
        self.counter_plus()

        # 爬取当前网页
        print('start parse : ' + response.url)
        if response.url in self.destination_list:
            self.destination_list.remove(response.url)

        if self.crawl_enable(response.url):
            item = SnspiderItem()
            for box in response.xpath('//div[@class="main-content w1240"]'):
                # article title
                item['newsTitle'] = box.xpath('.//h1[@class="main-title"]/text()').get()

                # article url
                item['newsUrl'] = response.url
                item['newsUrlMd5'] = self.md5(response.url)

                # article click time
                item['newsAuthor'] = box.xpath('.//a[@class="source"]/text()').get()

                # article publish time
                item['newsPublishTime'] = box.xpath('.//span[@class="date"]/text()').get()

                content = ""
                for s in box.xpath('.//div[@class="article"]//p/text()').getall():
                    s = s.replace(u'\u3000', u'')
                    content = content + s
                for s in box.xpath('.//div[@class="article"]//p/font/text()').getall():
                    s = s.replace(u'\u3000', u'')
                    content = content + s
                item['newsContent'] = content

                # 索引构建flag
                item['indexed'] = 'False'

                # yield it
                yield item

        # 获取当前网页所有url并宽度爬取
        urls = response.xpath('//a/@href').getall()
        for url in urls:
            real_url = urljoin(response.url, url)   # 将.//等简化url转化为真正的http格式url
            if real_url.startswith('http://'):  # 强制https
                real_url = real_url.replace('http://', 'https://')
            # if not real_url.startswith('https://news.sina.com.cn/'):
            if not self.crawl_enable(real_url):
                continue    # 保持爬虫在https://news.sina.com.cn/之内
            if real_url.endswith('.jpg') or real_url.endswith('.pdf'):
                continue    # 图片资源不爬
            if '.jsp?' in real_url:
                continue    # 动态网站不爬
            # md5 check
            md5_url = self.md5(real_url)
            # assert (self.binary_md5_url_search(md5_url) == -1) ^ (md5_url in self.url_md5_seen)
            if self.binary_md5_url_search(md5_url) > -1:    # 存在当前MD5
                pass
            else:
                self.binary_md5_url_insert(md5_url)
                self.destination_list.append(real_url)
                yield scrapy.Request(real_url, callback=self.parse, errback=self.errback_httpbin)

    def crawl_enable(self, url):
        for suffix in self.suffixes:
            if url.startswith(self.base_url + suffix) and url.endswith('.shtml'):
                return True
        return False

    def md5(self, val):
        import hashlib
        ha = hashlib.md5()
        ha.update(bytes(val, encoding='utf-8'))
        key = ha.hexdigest()
        return key



    # counter++，并在合适的时候保存断点
    def counter_plus(self):
        print('待爬取网址数：' + (str)(len(self.destination_list)))
        # 断点续爬功能之保存断点
        if self.counter % self.save_frequency == 0:  # 爬虫经过save_frequency次爬取后
            print('Rayiooo：正在保存爬虫断点....')

            f = open('./pause/response.seen', 'wb')
            pickle.dump(self.url_md5_seen, f)
            f.close()

            f = open('./pause/response.dest', 'wb')
            pickle.dump(self.destination_list, f)
            f.close()

            self.counter = self.save_frequency

        self.counter += 1  # 计数器+1

    # scrapy.request请求失败后的处理
    def errback_httpbin(self, failure):
        if failure.request._url in self.destination_list:
            self.destination_list.remove(failure.request._url)
        print('Error 404 url deleted: ' + failure.request._url)
        self.counter_plus()

    # 二分法md5集合排序插入self.url_md5_set--16进制md5字符串集
    def binary_md5_url_insert(self, md5_item):
        low = 0
        high = len(self.url_md5_seen)
        while (low < high):
            mid = (int)(low + (high - low) / 2)
            if self.url_md5_seen[mid] < md5_item:
                low = mid + 1
            elif self.url_md5_seen[mid] >= md5_item:
                high = mid
        self.url_md5_seen.insert(low, md5_item)

    # 二分法查找url_md5存在于self.url_md5_set的位置，不存在返回-1
    def binary_md5_url_search(self, md5_item):
        low = 0
        high = len(self.url_md5_seen)
        if high == 0:
            return -1
        while (low < high):
            mid = (int)(low + (high - low) / 2)
            if self.url_md5_seen[mid] < md5_item:
                low = mid + 1
            elif self.url_md5_seen[mid] > md5_item:
                high = mid
            elif self.url_md5_seen[mid] == md5_item:
                return mid
        if low >= self.url_md5_seen.__len__():
            return -1
        if self.url_md5_seen[low] == md5_item:
            return low
        else:
            return -1


