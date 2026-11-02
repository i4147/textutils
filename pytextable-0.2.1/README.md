pytextable - create latex tables using pure python
==================================================

[CI](https://github.com/karlch/pytextable/actions)
[![Codecov](https://codecov.io/github/karlch/pytextable/coverage.svg?branch=master)](https://codecov.io/github/karlch/pytextable?branch=master)
[Code style: black](https://github.com/ambv/black)

**pytextable** creates well-formatted latex tables with booktabs support in pure python.

**pytextable** is highly-configurable, you decide how your table should look.

**pytextable** is small, fast and requires nothing but python>=3.6.

Quick Start Guide
-----------------

1. Install

   ```
   pip install pytextable
   ```
2. Import

   ```
   import pytextable
   ```
3. Create a latex table from your data :)

   ```
   pytextable.write(data, "table.tex")
   ```

Example
-------

```
import pytextable

# This is usually your 2d numpy array or any sequence of sequences
DATA = [[1.2346, 1, 1.2346], [1.2346, 1.2346, 1.2346], [1.2346, 1.2346, 1.2346]]

>>> pytextable.tostring(
    DATA,
    fmt=".3f",
    header=("first", "second", "third"),
    caption="My fancy pytextable",
    label="tab:pytextable",
)
r"""
\begin{table}
    \centering
    \caption{My fancy pytextable}
    \label{tab:pytextable}
    \begin{tabular}{ccc}
        \toprule
        first & second & third \\
        \midrule
        1.235 & 1.000 & 1.235 \\
        1.235 & 1.235 & 1.235 \\
        1.235 & 1.235 & 1.235 \\
        \bottomrule
    \end{tabular}
\end{table}
"""

# To write to file use pytextable.write(DATA, filename)
>>> pytextable.write(DATA, "table.tex", fmt=".3f", ...)
```

Links
-----

* [Read the full documentation](https://pytextable.readthedocs.io/en/latest).
* [View the changelog](https://pytextable.readthedocs.io/en/latest/changelog.html).

License
-------

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <<http://www.gnu.org/licenses/>>.