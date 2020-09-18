from django.shortcuts import render, HttpResponse
import sys
from SN_IndexBuilder.query import Query

sys.path.append('..')
q = Query('../SN_index')

def search_form(request):
    return render(request, 'main.html')

def search(request):
    res = None
    if 'q' in request.GET and request.GET['q']:
        res, highlighted_results = q.standard_search(request.GET['q'])
        Content = {
            'query': request.GET['q'],
            'resAmount': len(res),
            'results': highlighted_results,
            'runtime': round(res.runtime, 6),
        }
    else:
        return render(request, 'main.html')

    return render(request, 'result.html', Content)