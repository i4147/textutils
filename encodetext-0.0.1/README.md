## Usage

```python
# Encoding
from encodetext import use

use.encode("hello world!")

# it turned out
#' 010111 000101 110110 110110 010100  010001 010100 001001 110110 110011 111111'

# Decoding
from encodetext import use

use.decode(" 010111 000101 110110 110110 010100  010001 010100 001001 110110 110011 111111")

# it turned out
# hello world;
```

