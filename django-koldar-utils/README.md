# Introduction

Generic django providing models and function used to better developer other apps.
In itself, this is **not** a django app 

```
pip install django-koldar-utils
```

# Upload new version

```
# pmakeup is a Massimo Bono project used to automatize the build; per se it is not necessary
pip install pmakeup 
add in TWINE_PYPI_PASSWORD the pypi password
pmakeup update-version-patch build upload-to-pypi
```