# django-rest-caller
Simple django templatetag for calling an urlconf view endpoint.

## Limitations

* it works only for GET methods
* it doesn't handle request without a body
* it doen't play nice with login required views (it assumes that the caller handles everything it is required to access the endpoint)
* it assumes that the endpoint returns a json

## Installation

Install with pip

```console
    $ python3 -m pip install django-rest-caller
```

Add `caller.apps.CallerConfig` to `INSTALLED_APPS`

```python
    INSTALLED_APPS = [
        ...
        'caller.apps.CallerConfig',
        ...
    ]
```

## Usage

### call

In your template load the templatetag

```html+django
    {% load caller_tags %}
```

and use the `call` tag as
```html+django
    {% call 'urlconf' arg1=42 arg2='X' with param1='1' param2='2' as 'object_name' %}
```
or
```html+django
    {% call 'urlconf' 42 'X' with param1='1' param2='2' as 'object_name' %}
```

* `'urlconf' arg1=42 arg2='X'` this is the usual {% url %} parameters (remember: use args parameter list or kwargs parameters, not both)
* `param1='1' param2='2'` these parameters will be converted to GET querystring
* `as 'object_name'` store the called object into object_name object. It can be a string or a variable name.

so the called url is equivalent to
```html+django
    {% url 'urlconf' arg1=42 arg2='X' %}?param1=1&param2=2
```

The `call` will inject the result json object into the template context, so you can

* use as context object

```html+django
    {% load caller_tags %}

    {% call 'api:blog-list' as 'posts' %}
    {% for post in posts %}
    <div>
    <h2>{{ post.title }}</h2>
    <p>{{ post.body }}</p>
    </div>
    {% endfor %}
```

* feeding to json tag

```html+django
    {% load caller_tags %}

    {% call 'api:blog-list' as 'posts' %}
    {{ posts|json_script:"posts-data" }}
    <script>
        function get_json(node) {
          var el = document.getElementById(node);
          return JSON.parse(el.textContent || el.innerText);
        }
        var posts = get_json("posts-data");
        console.log(posts);
    </script>
```

### json_script

This tag will backport the django >= 2.1 [`json_script`](https://docs.djangoproject.com/en/2.1/ref/templates/builtins/#json-script) filter,
which safely outputs a Python object as JSON, wrapped in a `<script>` tag, ready for use with JavaScript.

#### example

with
```python
    value = {'hello': 'world'}
```

and

```html+django
    {{ value|json_script:"hello-data" }}
```

will output

```html
    <script id="hello-data" type="application/json">{"hello": "world"}</script>
```

and can be retrieved with

```javascript
    function get_json(name) {
      var el = document.getElementById(name);
      return JSON.parse(el.textContent || el.innerText);
    }
    var data = get_json("hello-data");
    console.log(data);
```

## Changes

### dev

* proper url unquote arg parameters
* can use templatefilters in templatetag parameters

### 0.1.4

* show raised exception in called view instead of a generic one

### 0.1.3

* always require `as 'varname'`
* be able to use args or kwargs for urlconf as documented
* update documentation

### 0.1.1 - 0.1.2

* update documentation

### 0.1.0

* initial release
