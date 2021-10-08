# Introduction

Customizable backend that uses graphql to authenticate users.
Abstraction of a graphql authentication mechanism. 
This is an modification of `django-graphql-jwt`: I drop some functionalities that I did not care
and add capabilities that I needed.

Capabilities dropped:

 - cookies;
 
Capabilities added:

 - custom names and exceptions for authentication graphql mutrations/queries (needed for federations);
 - ability to customize authentication mechanism;
 - ability to work with graphene-federations when there are multiple authentication mechanisms;
 - ability to be easily extended;
 
# Motivation

I needed to work with graphene federations wehere there werre multiple graphqlk mutations with names like 
"login", "me", "refresdh_tokens" and so on.
`django-graphql-jwt` was more an hindrance than anything else since I need to authenticate via
a token rather tha username and password. In the end I ported the feature I needed from `django-graphql-jwt`
and created this variant.

This apps does not rely on its oiwn authentication mechanism, but just relay all the information 
it knows about the graphql request to the auithentication backend. In this way **you** are in charge
to perform authentication.

Still, the package provides some standard authentication mechanism you can use. 

# Installation

```
pip install django-graphql-apitoken
```

# Configuration

You need to add this app to the INSTALLED_APPS:

```
INSTALLED_APPS += "django_graphql_apitoken"
```

The second step is to create the authentication classes that graphene needs to be aware of.
Create a new file in your project root and add the following:


