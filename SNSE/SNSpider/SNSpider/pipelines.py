# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.utils.project import get_project_settings
import json
import pymysql
from twisted.enterprise import adbapi


settings = get_project_settings()


class SnspiderPipeline:
    def __init__(self):
        # connection database
        self.connect = pymysql.connect(host='127.0.0.1', user='root', passwd='1921885124Hu',
                                       db='sina')  # 后面三个依次是数据库连接名、数据库密码、数据库名称
        # get cursor
        self.cursor = self.connect.cursor()
        print("MySQL数据库连接成功")

    def process_item(self, item, spider):
        # sql语句
        insert_sql = """
        INSERT INTO pages(newsTitle, newsUrl, newsUrlMd5, newsAuthor, newsPublishTime, newsContent, indexed) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        # 执行插入数据到数据库操作
        try:
            self.cursor.execute(insert_sql, (item['newsTitle'], item['newsUrl'], item['newsUrlMd5'], item['newsAuthor'],
                                             item['newsPublishTime'], item['newsContent'], item['indexed']))
            # 提交，不进行提交无法保存到数据库
            self.connect.commit()
        except:
            # 如果发生错误则回滚
            self.connect.rollback()
            print('存入数据库失败')
        else:
            print('存入数据库成功')

        self.cursor.execute("SELECT COUNT(*) FROM pages")
        row_num = self.cursor.fetchone()[0]
        print("已收集%d条新闻\n" % row_num)

    def close_spider(self, spider):
        # 关闭游标和连接
        self.cursor.close()
        self.connect.close()


class SnspiderTwistedPipeline:
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):  # 函数名固定，会被scrapy调用，直接可用settings的值
        """
        数据库建立连接
        :param settings: 配置参数
        :return: 实例化参数
        """
        adbparams = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            port=settings['MYSQL_PORT'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,  # 指定cursor类型
            use_unicode=True
        )

        # 连接数据池ConnectionPool，使用pymysql或者Mysqldb连接
        dbpool = adbapi.ConnectionPool('pymysql', **adbparams)
        # 返回实例化参数
        return cls(dbpool)

    def process_item(self, item, spider):
        """
        使用twisted将MySQL插入变成异步执行。通过连接池执行具体的sql操作，返回一个对象
        """
        query = self.dbpool.runInteraction(self.do_insert, item)  # 指定操作方法和操作数据
        # 添加异常处理
        query.addCallback(self.handle_error)  # 处理异常
        return item

    def do_insert(self, cursor, item):
        # 对数据库进行插入操作，并不需要commit，twisted会自动commit
        insert_sql = """
        insert into pages(newsTitle, newsUrl, newsUrlMd5, newsAuthor, newsPublishTime, newsContent, indexed) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        self.cursor.execute(insert_sql, (item['newsTitle'], item['newsUrl'], item['newsUrlMd5'], item['newsAuthor'],
                                         item['newsPublishTime'], item['newsContent'], item['indexed']))

    def handle_error(self, failure):
        if failure:
            # 打印错误信息
            print(failure)


class JsonPipeline(object):
    def __init__(self):
        # 打开文件
        self.file = open('data.json', 'w', encoding='utf-8')

    # 该方法用于处理数据
    def process_item(self, item, spider):
        # 读取item中的数据
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        # 写入文件
        self.file.write(line)
        # 返回item
        return item

    # 该方法在spider被开启时被调用。
    def open_spider(self, spider):
        pass

    # 该方法在spider被关闭时被调用。
    def close_spider(self, spider):
        self.file.close()
