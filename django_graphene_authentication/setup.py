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
    test_dependencies=[
        "pytest"
    ]
)

setupper.perform_setup()