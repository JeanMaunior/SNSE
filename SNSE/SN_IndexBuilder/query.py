from whoosh.index import open_dir
from whoosh import qparser
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import sorting


class Query:
    def __init__(self, mydir=None):
        if mydir is None:
            self.ix = open_dir('index')
        else:
            self.ix = open_dir(mydir)
        self.searcher = self.ix.searcher()

    def search(self, parameter):
        # 从parameter中取出要执行搜索的字段（如newsContent, newsUrl）
        parser = None
        og = qparser.OrGroup.factory(0.5)
        list = parameter['keys']
        if len(list) == 1:
            parser = QueryParser(list[0], schema=self.ix.schema, group=og)
        elif len(list) > 1:
            parser = MultifieldParser(list, schema=self.ix.schema, group=og)
        parser.add_plugin(qparser.FuzzyTermPlugin())

        # sorting
        scores = sorting.ScoreFacet()
        date = sorting.FieldFacet("newsPublishTime", reverse=True)

        # 是否分页返回OR全部返回,默认全部返回
        _limit = None
        if 'page' in parameter and 'pagesize' in parameter:
            page = parameter['page']
            pagesize = parameter['pagesize']
            if page > 0 and pagesize != 0:
                _limit = page * pagesize

        # 执行搜索
        myquery = parser.parse(parameter['keywords'])
        results = self.searcher.search(myquery, limit=_limit, sortedby=[scores,date])
        # print(len(results))

        highlighted_results = []
        for hit in results:
            if 'newsAuthor' in hit:
                hit_list = {'newsTitle': hit.highlights('newsTitle'),
                            'newsUrl': hit['newsUrl'],
                            'newsAuthor': hit['newsAuthor'],
                            'newsPublishTime': hit['newsPublishTime'],
                            'newsContent': hit.highlights('newsContent')}

            else:
                hit_list = {'newsTitle': hit.highlights('newsTitle'),
                            'newsUrl': hit['newsUrl'],
                            'newsAuthor': ' ',
                            'newsPublishTime': hit['newsPublishTime'],
                            'newsContent': hit.highlights('newsContent')}
            highlighted_results.append(hit_list)
        return results, highlighted_results

    def standard_search(self, query):
        parameter = {
            'keys': ['newsTitle', 'newsContent'],
            'keywords': query,
            'page': 2,
            'pagesize': 10,
        }
        return self.search(parameter)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.searcher.close()
        print('Query close.')


