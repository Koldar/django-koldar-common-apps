from typing import Iterable, Tuple, List, Dict

import django_filters


def get_filters_from_filterset(filterset_type: type) -> Iterable[Tuple[str, django_filters.Filter]]:
    """
    get the instances of filters within a certain filter set

    :param filterset_type: a class extending django_filters.FilterSet
    :return: pair representing all the class attributes of filter_set typed as django_filters.Filter.
        Each pair is the name and the actual filter value within the set.
    """
    return filterset_type._meta.fields.keys()


def create_django_filter_class(filter_type_name: str, model_type: type, filters: Iterable[Tuple[str, django_filters.Filter]]):
    """
    Main method to dynamically create django filters,. We will output a class containing several filters.
    The output is something like this:

    .. ::code-block::

        class ProductFilter(django_filters.FilterSet):
            price = django_filters.NumberFilter()
            price__gt = django_filters.NumberFilter(field_name='price', lookup_expr='gt')
            price__lt = django_filters.NumberFilter(field_name='price', lookup_expr='lt')

            release_year = django_filters.NumberFilter(field_name='release_date', lookup_expr='year')
            release_year__gt = django_filters.NumberFilter(field_name='release_date', lookup_expr='year__gt')
            release_year__lt = django_filters.NumberFilter(field_name='release_date', lookup_expr='year__lt')

            manufacturer__name = django_filters.CharFilter(lookup_expr='icontains')

            class Meta:
                model = Product

    :param filter_type_name: name of the class generated in output
    :param model_type: django model that will be used to start the filtering
    :param filters: an iterable representing all the filters we want to create within this class.
        An example of items within this iterable may be:

        .. ::code-block
            filters=[
                ("price__gt", django_filters.NumberFilter(field_name='price', lookup_expr='gt')),
                ("price__lt", django_filters.NumberFilter(field_name='price', lookup_expr='lt')),
            ]


    .. ::seealso: https://django-filter.readthedocs.io/en/stable/guide/usage.html
    """

    meta = type(
        "Meta",
        (object, ),
        {
            "model": model_type
        }
    )

    properties = dict()
    for filter_name, filter_value in filters:
        properties[filter_name] = filter_value


    result = type(
        filter_type_name,
        (django_filters.FilterSet,),
        properties
    )
    return result



def create_django_filter_returning_one_value(filter_name: str, model_type: type, active_flag_name: str, fields: Dict[str, List[str]]) -> type:
    """
    Dynamically generates a django_toolbox filter that is garantueed to return at most a single value. This
    will automatically ignore inactive rows

    :param filter_name: part of the class name of the type to return. This string may be included as description of the filter.
        The output class name is "Filter{model_type}By{filter_name}" if there are at least one field in fields.
        Otherwise is it "Filter{model_type}"
    :param model_type: django_toolbox model where this filter applies
    :param fields: content to set in the "fields" meta class attribute
    :param active_flag_name: name of the active flag name
    :return: type representing the filter
    """

    meta = type(
        "Meta",
        (object,),
        {
            "model": model_type,
            "fields": fields
        }
    )

    def qs(self):
        parent = super(django_filters.FilterSet, self).qs

        result = parent.get(**{active_flag_name: True})
        return result

    if len(fields) > 0:
        filter_name = filter_name[0].upper() + filter_name[1:]
        filter_name = f"GetSingle{model_type.__name__}By{filter_name}Filter"
        description = f"""Fetch a single active {model_type.__name__} satisfying all constraint: {fields}"""
    else:
        filter_name = f"GetSingle{model_type.__name__}Filter"
        description = f"""Fetch a single active {model_type.__name__}"""

    filter_to_return = type(
        filter_name,
        (django_filters.FilterSet, ),
        {
            "__doc__": description,
            "Meta": meta,
            "qs": property(qs)
        }
    )

    return filter_to_return


def create_dynamic_active_django_filter(filter_name: str, model_type: type, active_flag_name: str, fields: Dict[str, List[str]]) -> type:
    """
    Dynamically generates a django filter. This will automatically ignore inactive rows

    :param filter_name: part of the class name of the type to return. This string may be included as description of the filter.
        The output class name is "Filter{model_type}By{filter_name}" if there are at least one field in fields.
        Otherwise is it "Filter{model_type}"
    :param model_type: django_toolbox model where this filter applies
    :param fields: content to set in the "fields" meta class attribute
    :param active_flag_name: name of the active flag name
    :return: type representing the filter
    """

    meta = type(
        "Meta",
        (object, ),
        {
            "model": model_type,
            "fields": fields
        }
    )

    def qs(self):
        parent = super(django_filters.FilterSet, self).qs

        result = parent.filter(**{active_flag_name: True})
        return result

    if len(fields) > 0:
        filter_name = filter_name[0].upper() + filter_name[1:]
        filter_name = f"GetAll{model_type.__name__}By{filter_name}Filter"
        description = f"""Fetch all active {model_type.__name__} by {fields}"""
    else:
        filter_name = f"GetAll{model_type.__name__}Filter"
        description = f"""Fetch all active {model_type.__name__}"""

    filter_to_return = type(
        filter_name,
        (django_filters.FilterSet, ),
        {
            "__doc__": description,
            "Meta": meta,
            "qs": property(qs)
        }
    )

    return filter_to_return

    # Example of a generated class
    # class F(django_filters.FilterSet):
    #     username = CharFilter(method='my_custom_filter')
    #
    #     class Meta:
    #         model = User
    #         fields = ['username']
    #
    #     def my_custom_filter(self, queryset, name, value):
    #         return queryset.filter(**{
    #             name: value,
    #         })