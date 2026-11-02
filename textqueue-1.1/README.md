TextQueue
================================================================================
TextQueue is a simple human readable file-based message queue.

The five core principals of TextQueue are
* To queue text based messages
* To be easily human readable
* To be easily human editable at rest
* To function directly on files without a daemon service
* To be forwards and backwards compatible with all versions of TextQueue

TextQueue Example
--------------------------------------------------------------------------------
```
-A queued message begins with a '-' dash control character
=A processed message begins with an '=' equals sign control character
!A message that encountered a critical error begins with an `!` exclamation mark control character
-Any message can have multiple lines
 where each sequential line begins with a ' ' space
=Any message can have multiple lines
 where each sequential line begins with a ' ' space
!Any message can have multiple lines
 where each sequential line begins with a ' ' space
# A comment begins with a '#' sign
# Multiline comments are possible using a space as the starting character on
  each sequential line.
# Messages are space sensitive, so the following message will read "  I have space padding  "
-  I have space padding  

-Blank lines are ingored
=Processed messages can apear after queued messages
-Message Variables
\Message variables are attached after a message
\A message can have any number of variables
\Message variables are fixed length and editable
\Additional space can be reserved for the message variable with trailing spaces   
\A single message variable cannot span multiple lines
# Comment Variables
\Comments can also have message variables
```

* `#` A comment these lines will be completely ignored
* `-` A message that has not yet been processed
* `=` A message that has been fully processed
* `!` A message that was processed but encountered a critical unrecoverable error
* ` ` A continuation of the previous message or comment from the previous line
* `\` A variable for the previous message which can be edited

Each line must match something like the regex
```
[-=# !\\][^\n]*(?:\n|<EOF>)|\n
```

Features
================================================================================

Comments
--------------------------------------------------------------------------------
Comments are a staple for any human readable file. They do not serve a purpose
for the machine reading or writing data, but they do allow for information to
be communicated to or by humans. It is possible that a user may use comments as
a way to extend the TextQueue syntax, but the syntax is already intended to be
extended with other control characters so this issue is not enough to offset
the benefits that comments bring to the spec.


Queued Messages
--------------------------------------------------------------------------------
Queued messages are messages that have not been processed. By default TextQueue
will only return these messages. A queued message should be marked complete
once it is done being processed. 


Completed Messages
--------------------------------------------------------------------------------
Completed messages are messages that have been marked as completed and do not
need to be processed further. By default completed messages are not returned
by TextQueue.


Critical Error Messages
--------------------------------------------------------------------------------
A message that was not completed but also should not be returned by TextQueue
again because there is a critical non-recoverable error with the message. By
default critical error messages are not returned by TextQueue.


Variables
--------------------------------------------------------------------------------
Variables unlock a large amount of utility by reserving space in the file for data to be saved per message.

Variables are limited to a single line and cannot be extended with the ` ` space control character to cross multiple lines.

Some examples of things variables can be used for are:
- Timestamps
- Error Codes
- Locking Mutexes
- Actor audit history
- Retry counts
- Multi-step state


Parallelism
================================================================================
TextQueue is not intended to have more than one reader and one writer at a time.

Some concurrent access is possible. Specifically a concurrent read and write.
The current schema loses some functionality with multiple concurrent reads.
Multiple concurrent writers would require a mutex lock using a separate mutex
file. If the user is so concurrent they need message-level concurrent writes,
then they are probably better off using a daemon based message passing solution
instead. A per-message mutex file could also be possible to allow for full
once-and-only-once MQTTT QOL2 style messages by using the message offsets in
the mutex. Adding a mutex file would not change or alter the current schema.

| Readers | Writers | Stability                                                             |
|---------|---------|-----------------------------------------------------------------------|
| 0       | 0       | Stable - At Rest                                                      |
| 1       | 0       | Stable - Only Reading                                                 |
| 0       | 1       | Stable - Only Writing                                                 |
| 1       | 1       | Stable when writes are appends and reads are not reading the final message|
| 2+      | 0+      | Unstable - Requires per-message mutex variable locks                  |
| 0+      | 2+      | Unstable - Requires file locking to prevent garbled append writes     |



Multiple User Mitigation - File Splitting
--------------------------------------------------------------------------------


Multiple User Mitigation - File Mutex
--------------------------------------------------------------------------------


Multiple User Mitigation - Message Mutex
--------------------------------------------------------------------------------
In order for a message to have a mutex a [variable] must be given to that
message. This means that in order to properly use this solution, every message
must have a variable used just for the mutex.

```tq
-Hello World
\mutex=      
-How are you today
\MUTEX
-Goodbye World
\MUTEX
```


Multiple Writer Mitigation - File Splitting
--------------------------------------------------------------------------------
If you want multiple writers to be able to write jobs in parallel then the
writers must be using different files to write to, or the write operations must
somehow be serialized to prevent overwriting each other.


Multiple Writer Mitigation - Mutex
--------------------------------------------------------------------------------
You can create a mutex for the entire file to prevent more than one program
from writing to it at once. This will require changes to the library to create,
release, and respect the mutex.


Multiple Reader Mitigation

Multiple Reader Mitigation - Mutex
--------------------------------------------------------------------------------
Mutex file using the message offset to block individual messages from being
read twice. This will require changes to the reader so that it can re-check
released mutexes to see if the mutex was released because the process crashed,
errored, or timed out or because it finished processing.

A mutex file just using the queue filename to prevent multiple people from
reading at once is less good becuase you will need to keep the file locked
until the processing is done.


Other Features and Discussion
================================================================================

Message Errors
--------------------------------------------------------------------------------
TextQueue supports labeling a message as having encountered a "critical
unrecoverable error" using the `!` critical error control character. Additional
error information should be handled by the user, either writing the error info
to a log, or storing some part of the error information in a preallocated
message variable.


Inserted Timestamps
--------------------------------------------------------------------------------
Inserted timestamps seem quite useful in some use cases. Some use cases do not
have, want, or need timestamps, meaning that timestamps should not be required.
The entire body of the message is an arbitrary utf8 string. With the only
restriction being the `\n` newline character, those require a following ` `
space to be included in the message. Any user who wanted timestamps could
easily create their own sub-schema for their own messages that included
timestamps. If or when we ever find a compelling reason to add timestamps as
first-class data, we can add a new control character for it.


Prefix Syntax [Redundant]
--------------------------------------------------------------------------------
Similarly to timestamps, we might want other forms of fixed metadata. We could
easily add this in the future by creating new control sequences that apply
their content to the following message, for example, an ISO 8601 prefix or a
unix epoch timestamp prefix.

```
T2024-06-13T19:26:15+00:00-Some message with an iso 8601 timestamp as metadata
T2024-06-13T19:26:15+00:00
-Also some message with an iso 8601 timestamp as metadata
U1718306775=Some completed message with a unix epoch timestamp
U1718306775
=Also some completed message with a unix epoch timestamp
```

Prefixes might stress backwards compatability though, parsing a newer queue
on an older parser would still work. However the prefix metadata would not
be associated with the message inside the parser and instead would be ignored.

To avoid this you can trigger an error when reading messages that have control
characters you do not recognize, specificlly breaking backwards compatability.
We may be able to do something to prevent this from causing an error, instead
making the entire line one line and having the entire message ignored, not
allowing prefixes to exist on their own line the way that ` ` space suffexes do.
Or by making a new control character to control all prefixes, such as `>`.
Getting that into the spec in the earliest version.

```
T2024-06-13T19:26:15+00:00-Some message with an iso 8601 timestamp as metadata
>T2024-06-13T19:26:15+00:00
-Also some message with an iso 8601 timestamp as metadata
```
Or requiring that prefixes on their own line have to be followed by a special
control sequence such as `>` before the next line.
```
T2024-06-13T19:26:15+00:00
>-Also some message with an iso 8601 timestamp as metadata
```

The same-line-only option seems pretty good honestly compared to the others


The control characters `T`, `U`, and `>` are not finalized and merits discussion.

> [!NOTE]
> This feature was implemented as Message Variables instead.

Fixed Metadata [Redundant] -> Tags
--------------------------------------------------------------------------------
Timestamps *could* be considered a special usecase. But we could also expand on
this functionality to allow for arbitrary metadata tags on messages.

```
*tagname:tagvalue
*source:john
*timestamp:1995 July 5th at 5:30pm
*language:en-us
-My Message
 and another line of my message
```

We can add arbitrary metadata tags like this as well if we find a compelling
reason to add them.

The control character `*` or syntax is not finalized and merits discussion.

> [!NOTE]
> This feature was implemented as Message Variables instead.


Retries
--------------------------------------------------------------------------------
There is a valid usecase where the user wants to show that a job is worth
retrying, but only worth retrying so many times. Therefore marking it as
processed, error, or leaving it queued would be incorrect. In order to avoid
reserving a bunch of control characters for each quantity of retry, we can
instead reserve one, such as `!`, followed by any number of arabic numerals and
use the prefix syntax style above. Arabic numerals will always decrease in
length as the value they represent approaches zero. We can confidently decrease
this number in-place until it reaches 0 without worrying about shifting the
offset of any other characters. Every time the item is pulled from the queue,
we can automatically decrease the number of retries.

```
!12-Some Queued message with 12 retries remaining
!08-Some queued message with 8 retries remaining, that used to have 10 or more
! 8-An alternative message syntax with 8 retries remaining that used to have 10 or more
!5=A processed message that still had 5 retries remaining when it was fully processed
```

The control character `!` or syntax is not finalized and merits discussion.

> [!NOTE]
> This feature was implemented as Message Varaibles instead


Editable Metadata
--------------------------------------------------------------------------------
We could add some sort user editable in-queue data. Much like the fixed
metadata before we could add some sort of editable tag system. This would come
with some additional restrictions, though. Primarily, a tag could never
increase in size beyond its original maximum size. Examples of things we could
put in editable metadata would be statuses, processed timestamps, error codes,
or retry counts. This would require some more planning before implementation,
but just like all the previous features, we could easily add it using a new
control character.


> [!NOTE]
> This feature was implmented as Message Variables instead


File Locking
--------------------------------------------------------------------------------
Locking the file so that multiple people are not writing to it at the same time
is a little complex. Because the file format can allow for multiple people to
write a byte of the file at the same time, as well as allow for a single person
to append to the end of the file while others are reading it, we want to be sure
that a lock system can accurately restrict the file without encumbering the
parallelism afforded to the text queue format.


Other
-------------
TextQueue plays nicely with other text-based serialized systems. Is lightweight
on the disk, only updating single characters or appending lines, and is easily
human manipulable.

Due to the nature of TextQueue's syntax, we do not need to escape any control
characters inside the message because each control character will start in the
first column of the message. Any control characters that exist inside the
message will be treated as their regular utf8 characters
Any newlines inside the message are treated as the end of the message. But if
the control sequence of the next line is a ` ` space, then that newline and the
next line are added to previous message.
If any new control characters need to be added in the future they will always
start in column 0, even if they need to extend to further columns down the
line later.


TextQueue does not have any specification for a lockfile making it not fully
thread safe yet, though there are some threadsafe guarantees that arise from
the current methodology.
* Any message that is being marked as processed will never be marked as queued
* Multiple message can be marked as processed simultaniously.

However it does not protect against:
* once and only once - Two processes reading the same control caracter, picking
  up the same message, and both marking the message as handled
* Manual human editable tools accessing the file, causing full file rewrites
  that can alter the entire saved state.




FAQ
================================================================================
**Q: Why do textqueue queue files not have schema or version numbers?**  
**A:** We intentionally excluded versions, instead making sure the schema is
forwards and backwards compatible forever. We rely on the starting character of
each line to determine functionality as a “control character”. The schema today
only consumes a few of the characters. We leave all the other utf8 characters
open to extend the syntax with other future features. However, adding new
control characters to the schema should be done with intention. If not, we
could enter a situation where we have added too many features with short
control sequences, and newer features would require multi-character
control sequences.

**Q: How do I put an error message for an unprocessable message in the queue?**  
**A:** The processor program should handle error messages for any message that
fails, probably in one of their logs. Error messages do not belong in the queue
itself. If we ever changed our minds about this, then the error messages would
still need to be stored in an external log file anyway, or risk shifting the
index of later messages. A possible in-queue solution could be fixed-length
error codes using something similar to editable metadata.

**Q: Will you support other languages?**  
**A:** The plan is for TextQueue to have support for multiple languages. One
way this might happen is for TextQueue to become a library with c bindings that
any language can call into, similarly to how most implementations of sqlite work.

**Q: Why do you allow message variables on comments?**  
**A:** Comments support multi line continuations and message variables to make
it easier for users to comment out a message. If comments are allowed to have
multiple lines and are allowed to have variables then all a user needs to do to
comment out a message is change the initial control character to a `#`. A side
effect it also makes parsing slightly easier as the logic to parse comments is
the same as the logic to parse all other messages.
