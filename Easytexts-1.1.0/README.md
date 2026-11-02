Easytexts: A Simple File Handler for Python

Install Easytexts using pip:

> pip install Easytexts

Usage:

Import the easytexts module:

> from Easytexts.Easytexts import \*

Writing and Appending:

append(file, text, newline=True, log=False): Appends text to a file, optionally adding a newline and logging the action.
Example:

> append("my\_file.txt", "This is a new line.")
> # Optional: Log the action
> append("my\_file.txt", "Another line!", log=True)

clear(file, text, replacement, log=False): Overwrites the entire content of a file with new text (replacement), optionally logging the action.
Example:

> clear("my\_file.txt", "This is the new content.n")

cide(file, text, log=False): Creates a new file and writes text to it, only if a file with the same name doesnt already exist, optionally logging the action.
Example:

> cide("new\_file.txt", "Hello, world!n")

Reading:

read(file, log=False): Reads the entire content of a file and returns it as a string, optionally logging the action.
Example:

> content = read("my\_file.txt")
> print(content)

Checking:

is\_empty(file, log=False): Checks if a file is empty, returning True if empty, False otherwise, optionally logging the result.
Example:

> if is\_empty("my\_file.txt"):
> :   print("The file is empty.")

Deleting:

delete(file, log=False): Deletes a file.
Example:

> delete("my\_file.txt")

Checking Existence:

does\_exist(file, log=False): Checks if a file exists, returning True if exists, False otherwise.
Example:

> if does\_exist("my\_file.txt"):
> :   print("The file exists.")

Disclaimer

While Easytext handles common errors and is suitable for learning and small projects, it's not intended for critical or demanding projects due to its limited scope and testing.

Additional Notes

The log parameter allows you to control if certain actions are logged (printed) for debugging or tracking purposes.
The newline parameter in append allows you to control whether a newline character is added before the appended text.

if you find any errors please let me know by making a poll on the github page ☺