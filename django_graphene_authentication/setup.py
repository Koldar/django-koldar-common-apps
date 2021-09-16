from django_koldar_utils.setuptools import library_setup


setupper = library_setup.LibraryScriptSetup(
    author="Massimo Bono",
    author_mail="massimobono1@gmail.com",
    description="A variant of djhango-graphql-jwt that can work with federations",
    keywords=["django", "graphql", "federation"],
    home_page="https://github.com/Koldar/django-koldar-common-apps",
    python_minimum_version=">=3.6",
    license_name="MIT",
    main_package="django_graphene_authentication",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    required_dependencies=[
        "Django>=3.2.5",
        "django-appconf>=1.0.4",
        "django-currentuser>=0.5.3",
        "django-filter>=2.4.0",
        "django-graphql-jwt>=0.3.2",
        "django-koldar-utils>=2.55.16",
        "django-polymorphic>=3.0.0",
        "graphene>=3.0b7",
        "graphene-django>=3.0.0b7",
        "graphene-django-extras>=0.5.2",
        "networkx>=2.5.1",
        "pydot>=1.4.2",
        "PyJWT>=2.1.0",
        "stringcase>=1.2.0",
    ],
    test_dependencies=[
        "pytest"
    ]
)

setupper.perform_setup()