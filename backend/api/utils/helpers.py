import json
from json import JSONDecodeError
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from urllib import parse

from django.template import Context, Template
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.response import Response

User = get_user_model()


def get_user_or_404(user_id):
    return get_object_or_404(User, pk=user_id)


def add_url_params(url, params: {}):
    url_parts = list(parse.urlparse(url))
    query = dict(parse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = parse.urlencode(query)
    return parse.urlunparse(url_parts)


def extract_from_request_json(request, key, default=None):
    """Extract data from the request object using given key.
    """
    try:
        request_body = json.loads(request.body)
    except JSONDecodeError:
        data = default
    else:
        data = request_body.get(key, default)
    return data


def extract_grade(request):
    return extract_from_request_json(request, "grade", default=4)


def no_review_data_response(card):
    error_message = f"The card id {card.id} is not in cram queue."
    response = Response({
        "status_code": 400,
        "detail": error_message
    }, status=status.HTTP_400_BAD_REQUEST)
    return response


def get_card_body(card, request):
    """Renders body using fields: Card.front Card.back and Card.template.
    Should be appended as a method to a serializer.
    """
    # is context_data necessary when rendering in a serializer?
    context_data = {
        "card": card,
        "request": request
    }
    if card.template:
        context = Context(context_data)
        template = Template(card.template.body, context)
        card_rendering = template.render(context)
    else:
        card_rendering = render_to_string("fallback.html", context_data)
    return card_rendering
