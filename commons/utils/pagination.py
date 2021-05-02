def create_pagination_url(url, limit=50, query_params=None):
    '''Method to create next pagination url.

    Args:
        url: URL to which pagination is to applied.
        limit: Number of records to fetch.
        query_params: Query params for pagination url.

    Returns:
        Updated next pagination url.
    '''

    next_pagination_url = f"{url}?limit={limit}"

    if query_params:
        query_params_string = ''

        for key, value in query_params.items():
            query_params_string = query_params_string + f"&{key}={value}"

        next_pagination_url = next_pagination_url + query_params_string

    return next_pagination_url
