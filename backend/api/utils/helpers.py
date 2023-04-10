from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from urllib import parse

User = get_user_model()


def get_user_or_404(user_id):
    return get_object_or_404(User, pk=user_id)

def add_url_params(url, params: {}):
    url_parts = list(parse.urlparse(url))
    query = dict(parse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = parse.urlencode(query)
    return parse.urlunparse(url_parts)