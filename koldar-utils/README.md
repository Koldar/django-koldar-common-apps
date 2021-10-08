# Introduction

Generic django providing models and function used to better developer other apps.
In itself, this is **not** a django app 

```
pip install django-koldar-utils
```

# Capabilities

 * `AbstractModelMetaclass` which can be used to create django models with abc capabilities;
 * `AbstractPermissionMixin` which does not rely on `groups` and `permissions` relationships;
 * `Orm` class that provides the creation of popular django fields, just for your convenience;
 * `ArrowAuditMixin` for providing `created_at` and  `updated_at` fields using `arrow` project;
 * convenience class to easily create django backends, middlesware, validators;
 * `ArrowField` implementation (taken from `django-arrow-field`);
 * convenience methods to interact with django framework without remembering how to do certain tasks;
 * classes used to create graphql CRUD operation easily;

# Upload new version

Use setup.py directly:

```
# create .pypirc in your home directory
python setup.py update_version_patch bdist_wheel upload
```

Or `pmake`:

```
# pmakeup is a Massimo Bono project used to automatize the build; per se it is not necessary
pip install pmakeup 
# add in TWINE_PYPI_PASSWORD the pypi password
pmakeup update-version-patch build upload-to-pypi
```
