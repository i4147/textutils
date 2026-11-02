reTexto
=======

Fast text processing for python

Run
---

> cd /[project\_path]
> docker build -t retexto .
> docker run -v $(pwd):/retexto:rw -it retexto bash

Basic Use
---------

```
if __name__ == '__main__':
s = '@Edux87, i need this www.google.com | https://github.com <br> \
<strong>UserName: çarlos </strong> \
i\'m from Perú 😛 \
#Friends #Text jajajajaja so fffunny  \
loooveee thiiis 😌😎 \
@florenciaflor19 Si!!! sé vo… 🐷JUANA🐷 \
smile! haha jejeje jojojo jujuju jijijijajaja 😂'
text = ReTexto(s)

s = text.remove_html() \
    .remove_mentions() \
    .remove_tags() \
    .remove_smiles(by='SMILING') \
    .convert_specials() \
    .convert_emoji() \
    .remove_nochars(preserve_tilde=True) \
    .remove_url() \
    .remove_duplicate(r='a-jp-z') \
    .remove_duplicate_vowels() \
    .remove_duplicate_consonants() \
    .remove_punctuation() \
    .remove_multispaces() \
    .lower() \
    .remove_stopwords() \
    .split_words(uniques=True)
print(s)
['username', 'from', 'love', 'i', 'ned', 'funy', 'juana', 'vo', 'this', 'si', 'im', 'se', 'peru', 'smile', 'so', 'smiling', 'carlos']
```