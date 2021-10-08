import abc
import re
from datetime import timedelta
from typing import List, Tuple, Any, Callable, Union, Optional

import traceback
import os
import inflection as inflection
import stringcase
from arrow import Arrow
from django.db import models

from django_koldar_utils.django_toolbox.fields.ArrowDateField import ArrowDateField
from django_koldar_utils.django_toolbox.fields.ArrowDurationField import ArrowDurationField
from django_koldar_utils.django_toolbox.fields.ArrowField import ArrowField


class INamingScheme(abc.ABC):
    """
    Interface representing a naming scheme for tables, relationships and foreign keys
    """

    @abc.abstractmethod
    def get_table_name(self, app_name: str, model_cls: str) -> str:
        pass

    @abc.abstractmethod
    def get_relationship_name(self, app_name: str, relationship_name: str, base_models: List[str]) -> str:
        pass

    @abc.abstractmethod
    def get_foreign_key_name(self, relationship_name: str, target_model: str) -> str:
        pass


class VerboseNamingScheme(INamingScheme):

    def get_table_name(self, app_name: str, model_cls: str) -> str:
        app_name = app_name.replace("_section", "")
        return f"{app_name}={model_cls}"

    def get_relationship_name(self, app_name: str, relationship_name: str, base_models: List[str]) -> str:
        app_name = app_name.replace("_section", "")
        return f"{app_name}={relationship_name}({','.join(base_models)})"

    def get_foreign_key_name(self, relationship_name: str, target_model: str) -> str:
        return f"id_{relationship_name}_{target_model}"


class StandardNamingScheme(INamingScheme):

    def get_table_name(self, app_name: str, model_cls: str) -> str:
        app_name = app_name.replace("_section", "")
        app_name_lc = stringcase.lowercase(app_name)
        model_cls_lc = stringcase.lowercase(model_cls)

        return f"{app_name_lc}.{model_cls_lc}"

    def get_relationship_name(self, app_name: str, relationship_name: str, base_models: List[str]) -> str:
        return f"{stringcase.lowercase(relationship_name)}_{'_'.join(map(stringcase.lowercase, base_models))}"

    def get_foreign_key_name(self, relationship_name: str, target_model: str) -> str:
        return stringcase.lowercase(f"id_{relationship_name}_{target_model}")


class Orm:

    _table_convention = "verbose"
    _naming_scheme = VerboseNamingScheme()

    @classmethod
    def set_table_naming_convention(cls, v: str):
        """
        Change the way each model table are generated.

        :param v: naming convention.
            - verbose: we use "=" inside table names and we generate relationships name as they were predicates
            - standard: we use "." in table names and we generate realtionship names by concatenating the table names with "_"
        """

        if v == "verbose":
            cls._naming_scheme = VerboseNamingScheme()
        elif v == "standard":
            cls._naming_scheme = StandardNamingScheme()
        else:
            raise ValueError(f"unindentified naming scheme {v}!")

        cls._table_convention = v

    DO_NOT_CREATE_INVERSE_RELATION = "+"
    """
    Value to put in a ForeignKeyField in "relateD_name". If you do this, the reverse relation won't be created at all 
    """

    @classmethod
    def get_current_app_name(cls) -> str:
        """
        Fetch the latest current app involved in the stacktrace.
        This function uses introspection of stacktrace to determine the application

        :return base directory of the app, which ususally is also the label of the app
        """
        for frame in reversed(list(filter(lambda x: "<string>" not in x, filter(lambda x: os.path.join("utils", "Orm.py") not in x,
                                                          filter(lambda x: "pydev" not in x,
                                                                 traceback.format_stack()))))):
            frame_str = str(frame)
            # something like "app_name/models.py"
            for f in ["models", "admin", "apps", "graphql_types", "mutations", "queries", "tests", "urls", "views"]:
                try:
                    index = frame_str.index(f + ".py")
                    file_name = frame_str[:index]
                    file_name = str(re.sub(r"^\s+File\s+\"", "", file_name))
                    app_name = os.path.basename(os.path.dirname(file_name))
                    return app_name
                except ValueError:
                    pass
        else:
            raise ValueError(f"Cannot find app name!")

    @classmethod
    def create_table_name(cls, model_cls: str) -> str:
        app_name = Orm.get_current_app_name()
        return cls._naming_scheme.get_table_name(app_name, model_cls)

    @classmethod
    def create_n_n_table_name(cls, name: str, basemodels: List[str]):
        """
        Create a new relationship name This name is the name fo the table representing the relationship name
        :param name:
        :param basemodels:
        :return:
        """
        app_name = Orm.get_current_app_name()

        result = []
        for m in basemodels:
            if isinstance(m, str):
                # the string may be of type "app_name.model". if so, remove the app_name part
                m = m.split(".")[-1]
                result.append(m)
            elif isinstance(m, type):
                result.append(type(m).__name__)
            else:
                raise TypeError(f"Invalid model type {type(m)}")

        return cls._naming_scheme.get_relationship_name(app_name, name, result)

    @classmethod
    def get_foreign_key_name(cls, relationship_name: str, target_model: str) -> str:
        return cls._naming_scheme.get_foreign_key_name(relationship_name, target_model)

    @staticmethod
    def generic_field_simple(field_type: type, null: bool, blank: bool, default: Union[Any, Callable[[], Any]],
                          help_text: str):
            """
            :param field_type: type of the field to create
            :param null: If True, Django will store empty values as NULL in the database
            :param blank: Note that this is different than null. null is purely database-related, whereas blank is
                validation-related. If a field has blank=True, form validation will allow entry of an empty value.
                If a field has blank=False, the field will be required.
            :param default: The default value for the field. This can be a value or a callable object.
                If callable it will be called every time a new object is created.
                You cannot use lambdas, but only named fields.
            :param help_text: Extra “help” text to be displayed with the form widget. It’s useful for documentation
                even if your field isn’t used on a form. The strnig is not HTML escaped.
            :return:
            """
            return Orm.generic_field(
                field_type=field_type,
                null=null,
                blank=blank,
                choices=None,
                db_column=None,
                db_index=False,
                default=default,
                error_messages=None,
                help_text=help_text,
                primary_key=False,
                unique=False,
                unique_for_date=None,
                unique_for_year=None,
                unique_for_month=None,
                verbose_name=None,
                validators=[],
                max_length=None
            )

    @staticmethod
    def generic_field(field_type: type, null: bool, blank: bool, choices: List[Tuple[Any, Any]], db_column: Optional[str], db_index: bool, default: Union[Any, Callable[[], Any]], error_messages: Optional[List[str]], help_text: str, primary_key: bool, unique: bool, unique_for_date: Optional[str], unique_for_month: Optional[str], unique_for_year: Optional[str], verbose_name: Optional[str], validators: List[Callable[[Any], None]], max_length: int):
        """
        :param field_type: type of the field to create
        :param null: If True, Django will store empty values as NULL in the database
        :param blank: Note that this is different than null. null is purely database-related, whereas blank is
            validation-related. If a field has blank=True, form validation will allow entry of an empty value.
            If a field has blank=False, the field will be required.
        :param choices: If choices are given, they’re enforced by model validation and the default form widget will
            be a select box with these choices instead of the standard text field.
        :param db_column: The name of the database column to use for this field. If this isn’t given,
            Django will use the field’s name
        :param db_index: If True, a database index will be created for this field.
        :param default: The default value for the field. This can be a value or a callable object.
            If callable it will be called every time a new object is created.
            You cannot use lambdas, but only named fields.
        :param error_messages: The error_messages argument lets you override the default messages that the
            field will raise. Pass in a dictionary with keys matching the error messages you want to overrid
        :param help_text: Extra “help” text to be displayed with the form widget. It’s useful for documentation
            even if your field isn’t used on a form. The strnig is not HTML escaped.
        :param primary_key: is True, the field is a primary key. primary_key=True implies null=False and unique=True.
            Only one primary key is allowed on an object.
        :param unique: If True, this field must be unique throughout the table.
        :param unique_for_date: Set this to the name of a DateField or DateTimeField to require that this field
            be unique for the value of the date field.
        :param unique_for_month: Like unique_for_date, but requires the field to be unique with respect to the month.
        :param unique_for_year: Like unique_for_date and unique_for_month.
        :param verbose_name: A human-readable name for the field
        :param validators:  A list of validators to run for this field
        :param max_length: in models like CharField, the length of the field
        :return:
        """
        d = dict(
            null=null,
            blank=blank,
            choices=choices,
            db_column=db_column,
            db_index=db_index,
            default=default,
            error_messages=error_messages,
            help_text=help_text,
            primary_key=primary_key,
            unique=unique,
            unique_for_date=unique_for_date,
            unique_for_month=unique_for_month,
            unique_for_year=unique_for_year,
            verbose_name=verbose_name,
            validators=validators,
            max_length=max_length,
        )
        return field_type(**d)

    @staticmethod
    def required_long_string(description: str) -> models.CharField:
        return Orm.generic_field(
            field_type=models.CharField,
            null=False,
            blank=False,
            default=None,
            help_text=description,

            choices=None,
            db_column=None,
            db_index=False,
            error_messages=None,
            primary_key=False,
            unique=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=255
        )

    @classmethod
    def relationship_many_to_many_with_intermediary_main_endpoint(cls, from_main_model: Union[str, type], to_secondary_model: Union[str, type],
                                         relationship_model: Union[str, type], related_name: str, help_text: str = None, through_fields: List[str] = None) -> models.ManyToManyField:
        """
        Used to define a N-N relationship that is using an intermediary model.
        Represents the manager that is used to fetch the "through" model.

        One author has many publications and each publication is made by many authors. Relationship is declared via an
        intermediary model called e.g., AuthorWritePublication.

        When modelling data in this manner, one endpoint needs to have this method. Usually you should choose the entity
        that is "on top/contains" to the other. In the author example, it is the author that **writes** a publication while the publication
        is more or less dependent w.r.t. the author. The author has an active role in the relation while the publication more of a passive role.
        Hence this method should be placed in author.

        The model field that stores the return value of this function should be something representing the other end of the
        relationship itself (**without considering the through model**) in a plural form (since this is a N-N relationship):
        in the example it should be something like "publications": you can then use "maria.publications.all()" to fetch all the publications
        she has written.

        If you want to retrieve "AuthorWritePublication" rather than "Publication", you should use the related_name
        you have chosen in "AuthorWritePublication.author" instead

        The related_name should have the same name as the resulting value of "relationship_many_to_many_with_intermediary_secondary_endpoint":
        basically, To work, "Author.writes.related_name" field needs to be the same of Publication return
        value of "relationship_many_to_many_with_intermediary_secondary_endpoint"

        .. ::code-block:: python
            class Author(models.Model):
                writes = Orm.relationship_many_to_many_with_intermediary_main_endpoint(
                    from_main_model="app.Author", to_secondary_model="app.Publication", relationship_model="app.AuthorWritePublication",
                    related_name="written_by"
                )

            class Publication(models.Model):
                written_by = Orm.relationship_many_to_many_with_intermediary_secondary_endpoint(
                    from_main_model="app.Author", to_secondary_model="app.Publication", relationship_model="app.AuthorWritePublication",
                )

            class AuthorWritePublication(models.Model):
                author = Orm.relationship_many_to_many_with_intermediary_reference_in_through(
                    to_model="app.Author",
                    on_delete=models.CASCADE,
                    related_name="writes_through_model")
                publication = Orm.relationship_many_to_many_with_intermediary_reference_in_through(
                    to_model="app.Publication",
                    on_delete=models.CASCADE,
                    related_name="written_by_through_model"
                )

        :param from_main_model: the active model: author. It is the one that "owns" the relationship.
            Should be representing this class.
        :param to_secondary_model: the passive model: publication
        :param help_text: help text
        :param through_fields: if the through model contains multiple foreign key to the same endpoint
            (e.g., author_chair_in_peer_review may be an addiotional foreign key of type Author in AuthorWritePublication),
            you need to specify here the names of the foreign key you want to use for vuilding the N-N relations. In the example,
            it is likely to be set to ["author", "publication"] which are the foreign key used in the relationship.
        :see https://docs.djangoproject.com/en/3.2/topics/db/models/#intermediary-manytomany:
        :see https://docs.djangoproject.com/en/3.2/topics/db/models/#many-to-many-relationships:
        :return:
        """

        return models.ManyToManyField(
            to_secondary_model,
            help_text=help_text,
            through=relationship_model,
            related_name=related_name
        )

    @classmethod
    def relationship_many_to_many_with_intermediary_secondary_endpoint(cls, from_main_model: Union[str, type], to_secondary_model: Union[str, type],
                                          relationship_model: Union[str, type], through_fields: List[str] = None) -> models.Manager:
        """
        Used to define a N-N relationship that is using an intermediary model.
        Represents the manager that is used to fetch the "through" model.

        One author has many publications and each publication is made by many authors. Relationship is declared via an
        intermediary model called e.g., AuthorWritePublication.

        When modelling data in this manner, all except one of the endpoints need to have this method
        (the main one should have relationship_many_to_many_with_intermediary_main_endpoint).
        Usually you should choose the entity that is "on bottom/dependent" to the main one. In the author example,
        it is the author that **writes** a publication while the publication
        is more or less dependent w.r.t. the author. The author has an active role in the relation while the publication more of a passive role.
        Hence this method should be placed in publication.

        The model field that stores the return value of this function should be the same as the "related_name" in the
        "relationship_many_to_many_with_intermediary_main_endpoint" function of the main relationship model
        (in this case Author).

        .. ::code-block:: python
            class Author(models.Model):
                writes = Orm.relationship_many_to_many_with_intermediary_main_endpoint(
                    from_main_model="app.Author", to_secondary_model="app.Publication", relationship_model="app.AuthorWritePublication",
                    related_name="written_by"
                )

            class Publication(models.Model):
                written_by = Orm.relationship_many_to_many_with_intermediary_secondary_endpoint(
                    from_main_model="app.Author", to_secondary_model="app.Publication", relationship_model="app.AuthorWritePublication",
                )

            class AuthorWritePublication(models.Model):
                author = Orm.relationship_many_to_many_with_intermediary_reference_in_through(
                    to_model="app.Author",
                    on_delete=models.CASCADE,
                    related_name="writes_through_model")
                publication = Orm.relationship_many_to_many_with_intermediary_reference_in_through(
                    to_model="app.Publication",
                    on_delete=models.CASCADE,
                    related_name="written_by_through_model"
                )

        :param from_main_model: model where the relationship starts. It is the one that "owns" the relationship
        :param to_secondary_model: model where the relaionship ends
        :param relationship_model: model of the through relationship
        :param through_fields: if the through model contains multiple foreign key to the same endpoint
            (e.g., author_chair_in_peer_review may be an addiotional foreign key of type Author in AuthorWritePublication),
            you need to specify here the names of the foreign key you want to use for vuilding the N-N relations. In the example,
            it is likely to be set to ["author", "publication"] which are the foreign key used in the relationship.
        :see https://gist.github.com/jacobian/827937#file-models-py:
        """
        pass

    @classmethod
    def relationship_many_to_many_with_intermediary_reference_in_through(cls, to_model: Union[str, type], on_delete,
                                                                         related_name: str) -> models.ForeignKey:
        """
        Used to define a N-N relationship that is using an intermediary model.
        Represents a field that is used in the intermediary table that actually represent the relation.

        One author has many publications and each publication is made by many authors. Relationship is declared via an
        intermediary model called e.g., AuthorWritePublication.

        When modelling data in this manner, the intermediary table has one column per entity involved in the
        relationship (in this case 2). This function needs to be called in AuthorWritePublication.

        The model field that stores the return value of this function should have a name of your choosing.
        Generally, you should choose a name representing the associated entity (e.g., for the author that has written
        a publication, it may be "author").
        The "related_name" you input here is **important**, since it is the name that you will used
        in the reference model to gain access to the list of intermediate models owned. For example, given an "author"
        if you want to fetch her associated AuthorWritePublication and if you have set "related_name" of "author" field
        in AuthorWritePublication to "has_written", you need to call "maria_user.has_written.all(). Generally,
        you should choose a name that represents the relationship entity (or the through model).
        In this case for publication it might be "written_by" and for author "involved_in_writing".
        If you want to retrieve the list of publications instead without dealing AuthorWritePublication, you should use
        use the fields storing the retuirn value of either "relationship_many_to_many_with_intermediary_main_endpoint"
        or "relationship_many_to_many_with_intermediary_secondary_endpoint".

        In the example, the AuthorWritePublication should have 2 fields storing the output of this function:
            publication = relationship_many_to_many_with_intermediary_reference_in_through("app.Publication", models.CASCADE, related_name="written_by")
            author = relationship_many_to_many_with_intermediary_reference_in_through("app.Author", models.CASCADE, related_name="writes")

        .. ::code-block:: python
            class Author(models.Model):
                writes = Orm.relationship_many_to_many_with_intermediary_main_endpoint(
                    from_main_model="app.Author", to_secondary_model="app.Publication", relationship_model="app.AuthorWritePublication",
                    related_name="written_by"
                )

            class Publication(models.Model):
                written_by = Orm.relationship_many_to_many_with_intermediary_secondary_endpoint(
                    from_main_model="app.Author", to_secondary_model="app.Publication", relationship_model="app.AuthorWritePublication",
                )

            class AuthorWritePublication(models.Model):
                author = Orm.relationship_many_to_many_with_intermediary_reference_in_through(
                    to_model="app.Author",
                    on_delete=models.CASCADE,
                    related_name="writes_through_model")
                publication = Orm.relationship_many_to_many_with_intermediary_reference_in_through(
                    to_model="app.Publication",
                    on_delete=models.CASCADE,
                    related_name="written_by_through_model"
                )

        :param to_model: model that is referenced by this field publication
        :param on_delete: what to do whenever a delete is performed
        :param related_name: inverse relation from "to_model" to gain access to this relationship
        :return:
        """
        return models.ForeignKey(to_model, on_delete=on_delete, related_name=related_name)

    # @classmethod
    # def relationship_many_to_many(cls, from_model: Union[str, type], to_model: Union[str, type],
    #                                      relationship_model: Union[str, type], related_name: str, help_text: str = None) -> models.ManyToManyField:
    #     """
    #     one author has many publications and each publication is made by many authros.
    #     This should be put in the "author". The model output name should be something repersenting the other end of the
    #     relationship itself (without considering the through model), so something like "authors".
    #     The related_name should have the same name as the resulting value of "relationship_many_to_many_inverse".
    #     :param from_model: author
    #     :param to_model: publication
    #     :param help_text: help text
    #     :return:
    #     """
    #     return models.ManyToManyField(
    #         from_model,
    #         help_text=help_text,
    #         through=relationship_model,
    #         related_name=related_name
    #     )
    #
    # @classmethod
    # def relationship_many_to_many_inverse(cls, from_model: Union[str, type], to_model: Union[str, type],
    #                                       relationship_model: Union[str, type]) -> models.Manager:
    #     """
    #     one author has many publications and each publication is made by many authros.
    #     This should be put in the "publications". The result value should be somethign repersenting
    #     the relationship, like "written_by"
    #     :param from_model: author
    #     :param to_model: publication
    #     :param help_text: help text
    #     :return:
    #     """
    #     pass

    @classmethod
    def relationship_many_to_many_simple(cls, from_model: Union[str, type], to_model: Union[str, type],
                                 relationship_name: str, related_name: str, help_text: str = None) -> models.ManyToManyField:
        """
        one author has many publications and each publication is made by many authros.
        This should be put in the "author"
        :param from_model: The model that specifies this function call (e.g., author)
        :param to_model: the model that has the corresponding relationship_many_to_many_simple_inverse publication
        :param on_delete: what to do whenever a delete is performed
        :param help_text: help text
        :param related_name: name of the inverse relations
        :return:
        """
        return models.ManyToManyField(
            to_model,
            help_text=help_text,
            related_name=related_name,
            db_table=Orm.create_n_n_table_name(relationship_name, [from_model, to_model])
        )

    @classmethod
    def relationship_many_to_many_simple_inverse(cls, from_model: Union[str, type], to_model: Union[str, type],
                                         relationship_name: str, help_text: str = None) -> models.Manager:
        """
        one author has many publications and each publication is made by many authros.
        This should be put in the "publications"
        :param from_model: author
        :param to_model: publication
        :param help_text: help text
        :return:
        """
        pass

    @classmethod
    def relationship_one_to_many(cls, single_model: Union[str, type], multi_model: Union[str, type],
                                 relationship_name: str) -> models.Manager:
        """
        one author has many contacts. This should be put in the "author" (but an authro has at least one contact).
        The relation needs to be positioned on the single_model entity

        :note:
        The name of the return value in the model must be the related name of the inverse relation

        :param single_model: author
        :param multi_model: contacts
        :param relationship_name: name of the relation
        :return:
        """
        pass

    @classmethod
    def relationship_one_to_many_inverse(cls, single_model: Union[str, type], multi_model: Union[str, type], on_delete,
                                         related_name: str, relationship_name: str, related_query_name: str = None, help_text: str = None) -> models.ForeignKey:
        """
        one author has many contacts. This should be put in the "contacts" (but an authro has at least one contact).

        :param single_model: author
        :param multi_model: contacts
        :param on_delete: what to do whenever a delete is performed
        :param related_name: name of the field that s the return value of :relationship_one_to_many: on the single_model
        :param related_query_name: name fo the django_toolbox query
        :param relationship_name: name of the "one to many" realtionship.
        :param help_text: help text
        :return:
        """
        return models.ForeignKey(
            single_model,
            on_delete=on_delete,
            help_text=help_text,
            null=False,
            related_name=related_name,
            related_query_name=related_query_name,
            db_column=Orm.get_foreign_key_name(relationship_name, single_model)
        )

    @classmethod
    def relationship_zero_to_many(cls, single_model: Union[str, type], multi_model: Union[str, type],
                                 relationship_name: str) -> models.Manager:
        """
        one author has many articles. This should be put in the "author". (but an authro can have zero articles)
        The relation needs to be positioned on the single_model entity

        :note:
        The name of the return value in the model must be the related name of the inverse relation

        :param single_model: author
        :param multi_model: contacts
        :param relationship_name: name of the relation
        :return:
        """
        pass

    @classmethod
    def relationship_zero_to_many_inverse(cls, single_model: Union[str, type], multi_model: Union[str, type], on_delete,
                                         related_name: str, relationship_name: str, related_query_name: str = None, help_text: str = None) -> models.ForeignKey:
        """
        one author has many articles. This should be put in the "article".  (but an authro can have zero articles)
        :param single_model: author
        :param multi_model: articles
        :param on_delete: what to do whenever a delete is performed
        :param related_name: name of the field that s the return value of :relationship_zero_to_many: on the single_model
        :param related_query_name: name fo the django_toolbox query
        :param relationship_name: name of the "one to many" realtionship.
        :param help_text: help text
        :return:
        """
        return models.ForeignKey(
            single_model,
            on_delete=on_delete,
            help_text=help_text,
            null=True,
            related_name=related_name,
            related_query_name=related_query_name,
            db_column=Orm.get_foreign_key_name(relationship_name, single_model),
        )

    @classmethod
    def relationship_one_to_one(cls, from_model: Union[str, type], to_model: Union[str, type], relationship_name: str, on_delete, related_name: str, related_query_name: str = None, help_text: str = None) -> models.OneToOneField:
        """
        one author has one name. This should be put in the "author"
        :param from_model: author
        :param to_model: name
        :param on_delete: what to do whenever a delete is performed
        :param help_text: help text
        :return:
        """
        return models.OneToOneField(
            to_model,
            on_delete=on_delete,
            help_text=help_text,
            null=False,
            blank=False,
            related_name=related_name,
            related_query_name=related_query_name,
            db_column=Orm.get_foreign_key_name(relationship_name, to_model),
        )

    @classmethod
    def relationship_one_to_one_inverse(cls, from_model: Union[str, type], to_model: Union[str, type],
                                        relationship_name: str) -> models.Manager:
        """
        one author has one name. This should be put in the "name"
        :param from_model: author
        :param to_model: name
        :return:
        """
        pass

    @classmethod
    def relationship_one_to_zeroone(cls, from_model: Union[str, type], to_model: Union[str, type], relationship_name: str, on_delete,
                                related_name: str, related_query_name: str = None, help_text: str = None) -> models.OneToOneField:
        """
        one author has one name. This should be put in the "author"
        :param from_model: author
        :param to_model: name
        :param on_delete: what to do whenever a delete is performed
        :param help_text: help text
        :return:
        """
        return models.OneToOneField(
            to_model,
            on_delete=on_delete,
            help_text=help_text,
            null=True,
            blank=True,
            related_name=related_name,
            related_query_name=related_query_name,
            db_column=Orm.get_foreign_key_name(relationship_name, to_model),
        )

    @classmethod
    def relationship_one_to_zeroone_inverse(cls, from_model: Union[str, type], to_model: Union[str, type],
                                        relationship_name: str, help_text: str = None) -> models.Manager:
        """
        one author has one name. This should be put in the "name"
        :param from_model: author
        :param to_model: name
        :param help_text: help text
        :return:
        """
        pass

    def required_indexed_string(self, description: str, default_value: Union[str, Callable[[], str]] = None, max_length: int = None) -> models.CharField:
        """
        Tells Django that the model has a string field. If default value is set, it is the value added to the database
        if the user does not provide a value. The field itself is non nullable. We will create an index for quick recovery

        :param description: text used to explain what the field does
        :param default_value: value to set the field to if the developer does not add a value by herself
        :param max_length: maximum number of hcaracters in the string. If left unspecified, it is 255
        :return: string type
        """
        if max_length is None:
            max_length = 255
        return Orm.generic_field(
            field_type=models.CharField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description,
            choices=None,
            db_column=None,
            db_index=True,
            error_messages=None,
            primary_key=False,
            unique=True,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=max_length
        )

    @classmethod
    def required_string(cls, description: str, default_value: Union[str, Callable[[], str]] = None, max_length: int = None) -> models.CharField:
        """
        Tells Django that the model has a string field. If default value is set, it is the value added to the database
        if the user does not provide a value. The field itself is non nullable

        :param description: text used to explain what the field does
        :param default_value: value to set the field to if the developer does not add a value by herself
        :param max_length: maximum number of hcaracters in the string. If left unspecified, it is 255
        :return: string type
        """
        if max_length is None:
            max_length = 255
        return Orm.generic_field(
            field_type=models.CharField,
            null=False,
            blank=False,
            choices=None,
            db_column=None,
            db_index=False,
            default=default_value,
            error_messages=None,
            help_text=description,
            primary_key=False,
            unique=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=max_length
        )

    @classmethod
    def required_email(cls, description: str, max_length: int = None, default_value: Union[str, Callable[[], str]] = None) -> models.EmailField:
        """
        Tells Django that the model has a string field. If default value is set, it is the value added to the database
        if the user does not provide a value. The field itself is non nullable

       :param description: text used to explain what the field does
        :param default_value: value to set the field to if the developer does not add a value by herself
        :param max_length: maximum number of hcaracters in the string. If left unspecified, it is 255
        :return: string type
        """
        if max_length is None:
            max_length = 255
        return Orm.generic_field(
            field_type=models.EmailField,
            null=False,
            blank=False,
            max_length=max_length,
            default=default_value,
            help_text=description,
            choices=None,
            db_column=None,
            db_index=False,
            error_messages=None,
            primary_key=False,
            unique=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
        )

    @classmethod
    def required_unique_string(cls, description: str, default_value: Union[str, Callable[[], str]] = None, max_length: int = None) -> models.CharField:
        """
        Tells Django that the model has a string field. If default value is set, it is the value added to the database
        if the user does not provide a value. The field itself is non nullable

        :param description: text used to explain what the field does
        :param default_value: value to set the field to if the developer does not add a value by herself
        :param max_length: maximum number of hcaracters in the string. If left unspecified, it is 255
        :return: string type
        """
        if max_length is None:
            max_length = 255
        return Orm.generic_field(
            field_type=models.CharField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description,
            unique=True,

            choices=None,
            db_column=None,
            db_index=False,
            error_messages=None,
            primary_key=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=max_length
        )

    @classmethod
    def nullable_string(cls, description: str, default_value: Union[str, Callable[[], str]] = None, max_length: int = None) -> models.CharField:
        """
        Tells Django that the model has a string field. If default value is set, it is the value added to the database
        if the user does not provide a value. The field itself may be null

        :param description: text used to explain what the field does
        :param default_value: value to set the field to if the developer does not add a value by herself
        :param max_length: maximum number of characters in the string. If left unspecified, it is 255
        :return: string type
        """
        if max_length is None:
            max_length = 255
        return Orm.generic_field(
            field_type=models.CharField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description,

            unique=False,
            choices=None,
            db_column=None,
            db_index=False,
            error_messages=None,
            primary_key=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=max_length
        )

    @classmethod
    def required_blank_string(cls, description: str, default_value: Union[str, Callable[[], str]] = None, max_length: int = None) -> models.CharField:
        if max_length is None:
            max_length = 255
        return Orm.generic_field_simple(
            field_type=models.CharField,
            null=False,
            blank=True,
            default=default_value,
            help_text=description
        )

    @classmethod
    def required_blank_text(cls, description: str,
                            default_value: Union[str, Callable[[], str]] = None) -> models.TextField:
        """
        Tells Django that the model has a text field: this means that it is a simple string that si assume to be very long.
        The field may be blank, but never null

        If default value is set, it is the value added to the database
        if the user does not provide a value. The field itself is non nullable

        :param description: text used to explain what the field does
        :param default_value: value to set the field to if the developer does not add a value by herself
        """
        return Orm.generic_field(
            field_type=models.TextField,
            null=False,
            blank=True,
            choices=None,
            db_column=None,
            db_index=False,
            default=default_value,
            error_messages=None,
            help_text=description,
            primary_key=False,
            unique=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=None
        )

    @classmethod
    def required_arrow_duration(cls, description: str = None, default_value: timedelta = None) -> ArrowDurationField:
        return ArrowDurationField(
            null=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def nullable_arrow_duration(cls, description: str = None, default_value: timedelta = None) -> ArrowDurationField:
        return ArrowDurationField(
            null=True,
            default=default_value,
            help_text=description
        )

    @staticmethod
    def required_duration(description: str, default_value: Union[timedelta, Callable[[], timedelta]] = None) -> models.DurationField:
        return Orm.generic_field_simple(
            field_type=models.DurationField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @staticmethod
    def required_datetime(description: str,
                          default_value: Union[Arrow, Callable[[], Arrow]] = None) -> ArrowField:
        """
        tell django_toolbox that this model has a date time that needs to be set
        """
        return Orm.generic_field_simple(
            field_type=ArrowField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @staticmethod
    def nullable_datetime(description: str,
                          default_value: Union[Arrow, Callable[[], Arrow]] = None) -> ArrowField:
        return Orm.generic_field_simple(
            field_type=ArrowField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description
        )

    @staticmethod
    def required_date(description: str,
                          default_value: Union[Arrow, Callable[[], Arrow]] = None) -> ArrowDateField:
        """
        tell django_toolbox that this model has a date that needs to be set
        """
        return Orm.generic_field_simple(
            field_type=ArrowDateField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @staticmethod
    def nullable_date(description: str,
                          default_value: Union[Arrow, Callable[[], Arrow]] = None) -> ArrowDateField:
        return Orm.generic_field_simple(
            field_type=ArrowDateField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def required_boolean(cls, description: str, default_value: Union[bool, Callable[[], bool]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.BooleanField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def nullable_boolean(cls, description: str,
                         default_value: Union[bool, Callable[[], bool]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.BooleanField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def required_int(cls, description: str,
                         default_value: Union[int, Callable[[], int]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.IntegerField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def nullable_int(cls, description: str,
                     default_value: Union[int, Callable[[], int]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.IntegerField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def required_long(cls, description: str,
                     default_value: Union[int, Callable[[], int]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.BigIntegerField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def nullable_long(cls, description: str,
                     default_value: Union[int, Callable[[], int]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.BigIntegerField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def required_bytes(cls, description: str,
                      default_value: Union[bytes, Callable[[], bytes]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.BinaryField,
            null=False,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def nullable_bytes(cls, description: str,
                      default_value: Union[bytes, Callable[[], bytes]] = None) -> models.BooleanField:
        return Orm.generic_field_simple(
            field_type=models.BinaryField,
            null=True,
            blank=False,
            default=default_value,
            help_text=description
        )

    @classmethod
    def required_external_id(cls, column_name: str = None, description: str = None, db_index: bool = False) -> models.BigIntegerField:
        """
        Represents an id that represents an object external from this database.
        For instance, if the users are stored in another database but you want to referecen a user from this local
        database, you can use this field

        :param column_name: name of the column to create
        :param description: help text of the column
        :param db_index: if true, we will create an index for the table
        """
        return Orm.generic_field(
            field_type=models.BigIntegerField,
            null=False,
            blank=False,
            choices=None,
            db_column=column_name,
            db_index=db_index,
            default=None,
            error_messages=None,
            help_text=description,
            primary_key=False,
            unique=False,
            unique_for_date=None,
            unique_for_year=None,
            unique_for_month=None,
            verbose_name=None,
            validators=[],
            max_length=None
        )

    @classmethod
    def primary_id(cls, column_name: str = None, description: str = None) -> models.BigAutoField:
        """
        create a rpimary id
        :param column_name: name of the column to create
        :return:
        """
        if column_name is None:
            column_name = "id"
        if description is None:
            description = "Unique Id representing the concept"
        return models.BigAutoField(db_column=column_name, primary_key=True, help_text=description)

    @classmethod
    def required_file(cls, upload_to: str, add_day: bool = False, format_str: str = None, description: str = None) -> models.FileField:
        """
        A file that needs to be set. The file will not be saved in the database itself, bt rather in a persistent storage
        (most likely a file system)

        :param upload_to: path of the storage where we are going to save the file
        :param add_day: if specified, we will add a date specified to the upload path in order to separate the upload
            files by time. Disabled by default
        :param format_str: the default time format to add if add_day is set. Defaults to "%Y/%m/%d"
        :param description: description of the field
        :return: file field upload
        """
        if not upload_to.endswith("/"):
            upload_to = upload_to + "/"
        if format_str is None:
            format_str = "%Y/%m/%d"
        if add_day is not None:
            upload_to = upload_to + format_str
        if not upload_to.endswith("/"):
            upload_to = upload_to + "/"
        return models.FileField(
            upload_to=upload_to,
            null=False,
            blank=False,
            help_text=description
        )

    @classmethod
    def nullable_file(cls, upload_to: str, add_day: bool = False, format_str: str = None,
                      description: str = None) -> models.FileField:
        """
        A file that can be null. The file will not be saved in the database itself, bt rather in a persistent storage
        (most likely a file system)

        :param upload_to: path of the storage where we are going to save the file
        :param add_day: if specified, we will add a date specified to the upload path in order to separate the upload
            files by time. Disabled by default
        :param format_str: the default time format to add if add_day is set. Defaults to "%Y/%m/%d"
        :param description: description of the field
        :return: file field upload
        """
        if not upload_to.endswith("/"):
            upload_to = upload_to + "/"
        if format_str is None:
            format_str = "%Y/%m/%d"
        if add_day is not None:
            upload_to = upload_to + format_str
        if not upload_to.endswith("/"):
            upload_to = upload_to + "/"
        return models.FileField(
            upload_to=upload_to,
            null=True,
            blank=False,
            help_text=description
        )

    @classmethod
    def image_with_default(cls, upload_to: str, default_image: str, description: str = None, **kwargs) -> models.ImageField:
        """
        create a field representing an image. The user may not specify any image: in this case the defulat image will be passed. The image will be stored in the specified storage location

        :param upload_to: the directory (if relative, relative to MEDIA_ROOT) where the image will be saved.
            see https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.FileField.upload_to
        :param default_image: name of the default image that will be used if no image is passed. It is a path
            (e.g., 'default.jpg') which depend on the django_toolbox storage chosen
        :param description: description of the field
        :param kwargs: other parameters to send to the ImageField
        """
        if description is None:
            description = f"Image representing the concept that will be saved in the {upload_to} storage"

        return models.ImageField(
            default=default_image,
            upload_to=upload_to,
            help_text=description,
            max_length=500,
            **kwargs
        )

