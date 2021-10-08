import abc
from typing import Optional

import stringcase


class ICrudOperationNamer(abc.ABC):
    """
    Class used to determine crud operation names
    """

    @abc.abstractmethod
    def get_create_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the create mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return: name of the create mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_create_return_value_name(self, django_type: type) -> Optional[str]:
        """
        Fetch the name corresponding to the return value of the create mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return return value of the creqte mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_all_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the read all query

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return: name of the read all query. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_all_return_value_name(self, django_type: type, django_filter_type: type) -> Optional[str]:
        """

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :param django_filter_type: type of a class representing a django_toolbox query set filter (the one that will be
        used to implement the read all query)
        :return: name of the return value fo the read all query. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_single_by_primary_key_name(self, django_type: type, primary_key_name: str) -> Optional[str]:
        """
        fetch the name corresponding to the read single by primary key mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :param primary_key_name: name of the primary key
        :return: name of the read single by primary key mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_single_by_primary_key_return_value_name(self, django_type: type, primary_key: str,
                                                         django_filter_type: type) -> Optional[
        str]:
        """
        fetch the name corresponding to the return value of read single by primary key mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :param primary_key: name fo the primary key of the model
        :param django_filter_type: type of a class representing a django_toolbox query set filter (the one that will be
        used to implement the read all query)
        :return: name of the return value of read single by primary key mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_update_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the update mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return: name of the update mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_update_return_value_name(self, django_type: type) -> Optional[str]:
        """
        fetch the return value name corresponding to the update mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return: name of the return value of update mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_delete_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the delete mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return: name of the delete mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_delete_return_value_name(self, django_type: type) -> Optional[str]:
        """
        fetch the return value name corresponding to the delete mutation

        :param django_type: type of the django_toolbox model (the one extending models.Model)
        :return: name of the return value of the delete mutation. If None we decide
        """
        pass


class StandardCrudOperationNamer(ICrudOperationNamer):
    """
    Default implementation generating standard CRUD names
    """

    def get_read_single_by_primary_key_return_value_name(self, django_type: type, primary_key_name: str,
                                                         django_filter_instance) -> Optional[
        str]:
        return None

    def get_update_return_value_name(self, django_type: type) -> Optional[str]:
        return None

    def get_delete_return_value_name(self, django_type: type) -> Optional[str]:
        return None

    def get_read_all_return_value_name(self, django_type: type, django_filter_type: type) -> Optional[str]:
        return None

    def get_create_name(self, django_type: type) -> Optional[str]:
        return f"Create{django_type.__name__}"

    def get_create_return_value_name(self, django_type: type) -> Optional[str]:
        return None

    def get_read_all_name(self, django_type: type) -> Optional[str]:
        return f"GetAll{django_type.__name__}"

    def get_read_single_by_primary_key_name(self, django_type: type, primary_key_name: str) -> Optional[str]:
        return f"Get{django_type.__name__}By{stringcase.pascalcase(primary_key_name)}"

    def get_update_name(self, django_type: type) -> Optional[str]:
        return f"UpdatePrimitive{django_type.__name__}"

    def get_delete_name(self, django_type: type) -> Optional[str]:
        return f"MarkInactive{django_type.__name__}"


class NamespacedCrudOperationNamer(ICrudOperationNamer):
    """
    An operation namer that prefix the name of query and mutations with a string. Useful in federated schemas,
    where multiple queries with similar names namy exist.
    """

    def __init__(self, prefix: str, suffix: str = None):
        """
        :param prefix: string to put before the model name in the query/mutation names
        :param suffix: string to put after the model name in the query/mutation names
        """
        self.prefix = stringcase.pascalcase(str(prefix))
        self.suffix = stringcase.pascalcase(str(suffix))

    def get_create_name(self, django_type: type) -> Optional[str]:
        return f"Create{self.prefix}{django_type.__name__}{self.suffix}"

    def get_create_return_value_name(self, django_type: type) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}{self.suffix}Created"

    def get_read_all_name(self, django_type: type) -> Optional[str]:
        return f"GetAll{self.prefix}{django_type.__name__}{self.suffix}"

    def get_read_all_return_value_name(self, django_type: type, django_filter_type: type) -> Optional[str]:
        return f"{self.prefix}{stringcase.camelcase(django_filter_type.__name__)}{self.suffix}"

    def get_read_single_by_primary_key_name(self, django_type: type, primary_key_name: str) -> Optional[str]:
        return f"Get{self.prefix}{django_type.__name__}By{stringcase.pascalcase(primary_key_name)}{self.suffix}"

    def get_read_single_by_primary_key_return_value_name(self, django_type: type, primary_key_name: str,
                                                         django_filter_type: type) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}By{stringcase.pascalcase(primary_key_name)}{self.suffix}"

    def get_update_name(self, django_type: type) -> Optional[str]:
        return f"UpdatePrimitive{self.prefix}{django_type.__name__}{self.suffix}"

    def get_update_return_value_name(self, django_type: type) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}{self.suffix}Updated"

    def get_delete_name(self, django_type: type) -> Optional[str]:
        return f"MarkInactive{self.prefix}{django_type.__name__}{self.suffix}"

    def get_delete_return_value_name(self, django_type: type) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}{self.suffix}Deleted"


class FederationCrudOperationNamer(NamespacedCrudOperationNamer):
    """
    Class tuned for federated schemas
    """

    def __init__(self, namespace: str):
        super().__init__(prefix=namespace, suffix="")