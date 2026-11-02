[![https://travis-ci.org/ojii/gettext.js.svg?branch=master](https://travis-ci.org/ojii/gettext.js.svg?branch=master)](https://travis-ci.org/ojii/gettext.js)
[![Documentation Status](https://readthedocs.org/projects/gettextjs/badge/?version=latest)](http://gettextjs.readthedocs.org/en/latest/?badge=latest)

gettext.js
----------

GNU gettext in Javascript. Compile your mo files to JSON/JS and then use them
directly from Javascript in your browser.

Demo: <https://cdn.rawgit.com/ojii/gettext.js/master/demo/index.html>

Docs: <http://gettextjs.readthedocs.org/>

### Usage

#### Compiling

```
Usage:
    gettextjs [-i] [-v] [--js] <locale-path> [<out-dir>]

Options:
    -h --help       Show this screen.
    --version       Show version.
    -i --indent     Indent JSON file.
    -v --verbose    Print stuff while doing work.
    --js            Compile to JS instead of JSON.
```

#### Javascript

##### Async from JSON

```
Gettext.load('/base/url/to/locale', 'en', 'messages').then(function(gettext){
    var msgstr = gettext.gettext('msgid');
});
```

##### Sync from JS

```
var gettext = new Gettext(EN_MESSAGES);
var msgstr = gettext.gettext('msgid');
```