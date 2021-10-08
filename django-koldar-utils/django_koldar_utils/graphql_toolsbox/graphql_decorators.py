import logging

LOG = logging.getLogger(__name__)


class graphql_subquery:
    """
    Class decorator to include a class in the global GraphQL query
    """
    query_classes = []

    def __init__(self, cls):
        self.cls = cls
        LOG.info(f"Registering query {cls}")
        graphql_subquery.query_classes.append(cls)

    def __call__(self, *args, **kwargs):
        return self.cls()


class graphql_submutation:
    """
    Class decorator to include a class in the global GraphQL query
    """
    mutation_classes = []

    def __init__(self, cls):
        self.cls = cls
        LOG.info(f"Registering mutation {cls}")
        graphql_submutation.mutation_classes.append(cls)

    def __call__(self, *args, **kwargs):
        return self.cls(*args, **kwargs)
