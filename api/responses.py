import json

from django.core.paginator import Paginator
from django.http import JsonResponse


API_VERSION = 'v1'


def api_response(data=None, meta=None, message='', status=200):
    payload = {
        'success': 200 <= status < 400,
        'version': API_VERSION,
        'message': message,
        'data': data if data is not None else {},
    }
    if meta is not None:
        payload['meta'] = meta
    return JsonResponse(payload, status=status, json_dumps_params={'ensure_ascii': False})


def api_error(message, errors=None, status=400, code='bad_request'):
    return JsonResponse(
        {
            'success': False,
            'version': API_VERSION,
            'message': message,
            'error': {
                'code': code,
                'details': errors or {},
            },
        },
        status=status,
        json_dumps_params={'ensure_ascii': False},
    )


def read_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode(request.encoding or 'utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def positive_int(value, default, minimum=1, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def paginate_queryset(queryset, request, default_page_size=24, max_page_size=100):
    page_size = positive_int(request.GET.get('page_size'), default_page_size, 1, max_page_size)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(positive_int(request.GET.get('page'), 1))
    meta = {
        'page': page_obj.number,
        'page_size': page_size,
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    }
    return page_obj, meta
