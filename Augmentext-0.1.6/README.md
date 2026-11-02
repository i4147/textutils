![Augmentext](https://raw.githubusercontent.com/mdbloice/AugmentorFiles/master/Augmentext/Augmentext-Logo.png)

Text augmentation package for NLP applications in the biomedical domain.

**Augmentext is work in progress!** However, the features that are available are stable.

## Installation Information

[![Augmentext](https://github.com/mdbloice/Augmentext/workflows/Augmentext/badge.svg)](https://github.com/mdbloice/Augmentext/actions?query=workflow%3AAugmentext)
[![Supported Python Versions](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue.svg)](https://pypi.python.org/pypi/Augmentext)
![PyPI](https://img.shields.io/pypi/v/Augmentext)

Augmentext is compatible with Python 3 only (Python 3.6 or greater is required).

## Features

- Auto-generated, randomised misspellings
- Dictionary-based thesaurus word replacement
- Auto-generated abbreviations
- More to come...

### Biomedical Domain Specific Features

Although a general library, Augmentext has a special focus on biomedical text.

- Replacement of mm/g^2 with common mistakes, e.g. g/mm^2 etc.
- Conversion of units from metric to imperial/customary and vice versa
- Integration of SNOMED, ICD, MeSH, RxNorm and other text corpora in to the augmentation pipeline
- Synonym replacement using pre-trained models using GloVe, fasttext, and word2vec.

### Medical RegEx Repository

Augmentext includes a database of useful regular expressions for use in medical NLP applications. These can be accessed indepently of using Augmentext to augment your data. 

For example: 

```python
from Augmentext import MedRegEx

mre = MedRegEx()

mre.print_summary()
```

This will print all available regular expressions with use cases. See the main documentation for more details.

## Usage

*For complete documentation, please see <https://augmentext.readthedocs.io>*

Augmentext is text augmentation library that is designed to be be easy to use and aims at providing functions suitable for work in the biomedical domain.

### Pipelines

Augmentext uses the concept of a *Pipeline* to augment your data. You use Augmentext by first creating a Pipeline object, which you provide with your initial data, and then add operations to this Pipeline.

As text is passed through this Pipeline, the operations are applied to the text stochastically, according to user-defined probabilities.

For example:

```python
from Augmentext import Pipeline

# Create a Pipeline object
p = Pipeline("/path/to/text_files", extension="txt")

# Add some operations
p.swap_random_words(probability=0.3)
p.swap_random_characters(1.0)

# Sample some new data
p.sample(100)
```

This will sample 100 new data augmented from your data set.

Pipelines can be created in any order, with as many repititions as required, and in any configuration. However, care should be taken with the order in which certain operations appear: it would not make much sense to insert random misspellings before trying to perform a drug synonym swap.

## Data Input

Augmentext expects your data to be formatted in a certain way, in order to facilitate the features of the software.

A corpora is a collection of documents. Each document is a single file. Each documents needs to have paragraphs seperated by two newline characters `'\n'`, for example as follows:

`cicero.txt`:

>Non eram nescius, Brute, cum, quae summis ingeniis exquisitaque doctrina philosophi Graeco sermone tractavissent, ea Latinis litteris mandaremus, fore ut hic noster labor in varias reprehensiones incurreret. nam quibusdam, et iis quidem non admodum indoctis, totum hoc displicet philosophari. quidam autem non tam id reprehendunt, si remissius agatur, sed tantum studium tamque multam operam ponendam in eo non arbitrantur. erunt etiam, et ii quidem eruditi Graecis litteris, contemnentes Latinas, qui se dicant in Graecis legendis operam malle consumere. postremo aliquos futuros suspicor, qui me ad alias litteras vocent, genus hoc scribendi, etsi sit elegans, personae tamen et dignitatis esse negent. Contra quos omnis dicendum breviter existimo.
>
>Quamquam philosophiae quidem vituperatoribus satis responsum est eo libro, quo a nobis philosophia defensa et collaudata est, cum esset accusata et vituperata ab Hortensio. qui liber cum et tibi probatus videretur et iis, quos ego posse iudicare arbitrarer, plura suscepi veritus ne movere hominum studia viderer, retinere non posse. Qui autem, si maxime hoc placeat, moderatius tamen id volunt fieri, difficilem quandam temperantiam postulant in eo, quod semel admissum coerceri reprimique non potest, ut propemodum iustioribus utamur illis, qui omnino avocent a philosophia, quam his, qui rebus infinitis modum constituant in reque eo meliore, quo maior sit, mediocritatem desiderent.
>
>Sive enim ad sapientiam perveniri potest, non paranda nobis solum ea, sed fruenda etiam est; sive hoc difficile est, tamen nec modus est ullus investigandi veri, nisi inveneris, et quaerendi defatigatio turpis est, cum id, quod quaeritur, sit pulcherrimum. etenim si delectamur, cum scribimus, quis est tam invidus, qui ab eo nos abducat? sin laboramus, quis est, qui alienae modum statuat industriae? nam ut Terentianus Chremes non inhumanus, qui novum vicinum non vult 'fodere aut arare aut aliquid ferre denique' non enim illum ab industria, sed ab inliberali labore deterret, sic isti curiosi, quos offendit noster minime nobis iniucundus labor.

Loading `cicero.txt` will result in a corpus containing 1 document, 3 paragraphs, and 13 sentences.

## Medical Terminologies

Augmentext includes ICD, MeSH, and SNOMED-based functionality.

The Augmentext package does not include the terminologies, and must be provied by the user.

Place the data into the **Augmentext home directory** (Linux/macOS: `/home/username/.augmentext/` Windows: `C:\Users\username\.augmentext\`)

Linux and macOS:

- MeSH: `/home/username/.augmentext/mesh/`
- ICD: `/home/username/.augmentext/icd/`
- SNOMED: `/home/username/.augmentext/snomed/`
- etc.

Windows:

- MeSH: `C:\Users\username\.augmentext\mesh\`
- ICD: `C:\Users\username\.augmentext\icd\`
- SNOMED: `C:\Users\username\.augmentext\snomed\`
- ...

A full list of supported terminologies is provided in the help pages.

Custom terminologies are also possible.

The terminologies above require you agree to licence agreements and to register in order to download them.

Users in the US can download SNOMED from here: <https://www.nlm.nih.gov/healthit/snomedct/international.html>
Users in other countries will need to contact SNOMED.

If the default directories are not suitable, supply a user-defined path as follows:

```python
from Augmentext import Pipeline

p = Pipeline("./path/to/data")
p.set_augmentext_home("/var/user/path/augmentext")
```

## Non-Medical Terminologies
Non-medical terminologies include, for example, WordNet.

As these terminologies are open, Augmentext can download them for you.

## Extending Augmentext

Because NLP is a field with many niche applications and problem domains, Augmentext has been designed to be highly extensible.

For example, say you wish to add a custom operation to your Pipeline that reversed text, you only need to create a new class that uses the Operation class as its parent class, and implement the function `perform_operation()`. Therefore, you could say:

```python
from Augmentext.Operations import Operation


class ReverseText(Operation):
    def __init__(self, probability):
        super().__init__(probability)

    def perform_operation(self, text):
        return text[::-1]
```

This custom operation can now be added to a pipeline as follows:

```python
from Augmentext import Pipeline

p = Pipeline("/path/to/data")

# Add your custom operation to your pipeline:
r = ReverseText(probability=0.5)
p.add_operation(r)

p.sample(100)
```

This will work as long as your custom operation is of type Operation.

## Tests

To execute the tests, run:

```sh
$ py.test-3 -v
```

from the command line within the project's root folder (this command may differ depending on your system's setup). Install pytest via `sudo apt install python3-pytest`.

Augmentext is intended for use on Python 3 only.

## References and Resources

Initial thoughts based on description at <https://github.com/oxinabox/MultiResolutionIterators.jl>.

For example, the package above says the following:

>There are many different ways to look at text corpora.
>
>The true structure of a corpus might be:
> - **Corpus**
> - made up of: **Documents**
> - made up of: **Paragraphs**
> - made up of: **Sentences**
> - made up of: **Words**
> - made up of: **Characters**
>
>Very few people want to consider it at that level.
> - Someone working in **Information Retrieval** might want to consider the corpus as **Corpus made up of Documents made up of Words**.
> - Someone working on **Language Modeling** might want to consider **Corpus made up of Words**
> - Someone working on **Parsing** might want to consider **Corpus made up Sentences made up of Words**.
> - Someone training a **Char-RNN** might want to consider **Corpus made up of Characters**.
>
>This package lets you better work with iterators of iterators to allow them to be flattened and viewed at different levels.
