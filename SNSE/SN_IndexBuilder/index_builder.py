from whoosh.fields import Schema, ID, TEXT, NUMERIC
from whoosh.index import create_in, open_dir
from jieba.analyse import ChineseAnalyzer
import pymysql
import settings


class IndexBuilder:
    def __init__(self):
        # connection database
        self.connect = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, passwd=settings.MYSQL_PASSWORD,
                                       db=settings.MYSQL_DBNAME)
        # get cursor
        self.cursor = self.connect.cursor()
        print("MySQL connected.")

    def build_index(self):
        analyzer = ChineseAnalyzer()

        # build schema
        schema = Schema(
            newsId = ID(stored=True),
            newsTitle = TEXT(stored=True, analyzer=analyzer),
            newsUrl = ID(stored=True),
            newsAuthor = TEXT(stored=True, analyzer=analyzer),
            newsPublishTime = TEXT(stored=True),
            newsContent = TEXT(stored=True, analyzer=analyzer),
        )

        # open index directory
        import os.path
        if not os.path.exists('../SN_index'):
            os.mkdir('../SN_index')
            ix = create_in('../SN_index', schema)
            print('index索引已创建')
        else:
            ix = open_dir('../SN_index')
            print('index已载入')

        # build index
        writer = ix.writer()
        indexed_amount = 0
        self.cursor.execute("SELECT COUNT(*) FROM pages")
        total_amount = self.cursor.fetchone()[0]
        self.cursor.execute(" SELECT COUNT(*) FROM pages WHERE indexed='False' ")
        false_amount = self.cursor.fetchone()[0]
        print(false_amount, '/', total_amount, '待处理')

        select_sql = "SELECT * FROM pages WHERE indexed='False' LIMIT 1"
        update_sql = "UPDATE pages SET indexed='True' WHERE newsTitle=%s"
        while True:
            try:
                self.cursor.execute(select_sql)
                row = self.cursor.fetchone()
                if row is None:
                    print('无待处理文件')
                    break
                writer.add_document(
                    newsTitle = row[0],
                    newsUrl = row[1],
                    newsAuthor = row[3],
                    newsPublishTime = row[4],
                    newsContent = row[5],
                )
                self.cursor.execute(update_sql, (row[0]))
                self.connect.commit()
                writer.commit()
                writer = ix.writer()
                indexed_amount += 1
                print(indexed_amount, '/', false_amount, '/', total_amount)
            except:
                print('MySQL读取异常')
                print('已处理', indexed_amount, '/', total_amount, '项.')
                break

        writer.commit(optimize=True)
        print('Index Completed!')
        # 关闭游标和连接
        self.cursor.close()
        self.connect.close()


if __name__ == '__main__':
    id = IndexBuilder()
    id.build_index()
