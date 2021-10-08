from koldar_utils.setuptools_toolbox.library_setup import LibraryScriptSetup

s = LibraryScriptSetup(
    author_mail="massimobono1@gmail.com",
    author="Massimo Bono",
    description="Yet another tool to generate GraphQL CRUD operations",
    keywords=["django", "graphql", "crud", "automatic generation"],
    home_page="https://github.com/Koldar/django-koldar-common-apps",
    python_minimum_version=">=3.6",
    license_name="mit",
    main_package="django_graphene_crud_generator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)

if __name__ == "__main__":
    s.perform_setup()
