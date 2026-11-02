# cptextract
---
A Python package to automate extraction of cone penetration test (CPT) data from various sources.

## Description
`cptextract` is a library of function and class to help extract Cone Penetration Test (CPT) data from csv and Excel files that are store inconsistenly. For example:
- cpt data with different data headers or labels
- cpt data stored in different Excel sheets names
- cpt data table not starting at the first row
- cpt data stored in units of kPa instead of MPa

### Limitations
This package has been developed based on example data found on the New Zealand Geotechnical Database. Some other limitations include:
- only extracts Depth, Cone tip resistance (qc), Friction resistance (fs) and U2 pore pressure (u2)
- only works with units of meter for depth; and MPa or kPa for qc,fs and u2
- accepted file types are .csv, .xls and .xlsx

### Installation
```bash
pip install cptextract
```

## Usage
Please refer to example [notebook](https://github.com/geocodes-eng/cptextract). 

## Contributors
TBC