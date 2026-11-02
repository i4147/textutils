## Introduction 

> text2numb is a simple python module for converting text to numbers and back again. It can be used for cryptography, compression or anything else that you can think of. 

## Basic Tutorial
In order to convert text into numbers, you have to call the `text2numb(...)` function. An example is shown below:

`>>> import text2numb  ` \
`>>> num = text2numb.text2numb('Hello, world!')`\
`>>> num` \
`5735816763073854953388147237921`

In order to convert this back to plain text, all we need to do is call the `numb2text(...)` function.

`>>> txt = text2numb.numb2text(num)` \
`>>> txt` \
`Hello, world!`

## The Setup Function

Every time text2numb is imported, a function called `setup(...)` is run. This function sets the `int_max_str_size` using the sys function `sys.set_int_max_str_size`. It is important that this is called, otherwise errors may occour when trying to convert large amounts of data. However, if for whatever reason you need to change this back to the origional value, you can by using 
`text2numb.setup(text2numb.max_before_setup)`

## Backend Workings :gear: 

The code behind text2numb uses the base64 module base-changing functions in order to convert text to numbers. Text is encoded using base64's implementation of base 16, then decoded using functions defined within the module. The result is a number! And by reversing the process, this module can convert numbers back to text. \
       \
If you want to convert a number into any base, you can use the `_int2base(...)` function. An example is shown below:  \
     \
`>>> text2numb._int2base(14, 9)` \
`'15'`

In order to convert this back, you can use:

`>>> int('15', 9)` \
`14`

In addition to `_int2base(...)`, there are two other backend functions - `_enc_num(...)` and `_dec_num(...)`. These functions are called by `text2numb(...)` and `numb2text(...)`, and serve as the actual computing functions. If for whatever reason you want to call them directly, they take the same arguments as `text2numb(...)` and `numb2text(...)` ("string" for `_enc_num(...)` and "integer" for `_dec_num(...)`.

## Credits

The credits for the function "_int2base" go to:\
**Alex Huszagh & Alex Martelli** on StackOverflow.com\
Their StackOverflow awnser (and the question) can be found here:\
[https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base?r=SearchResults&s=1%7C235.2771](url)\
The author of this python module did not ask the origional question.\
\
The credits for the rest of the code go to: \
Pigeon Nation