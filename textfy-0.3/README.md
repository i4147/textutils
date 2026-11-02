# Textfy
- Send SMS message using "Twilio"

## How to use
1. Using decorator
- Wrap function with decorator ```@Textfy()```
- Wrapped function needs to return a dictionary which contains message body to send
- When using decorator, it will also sends the execution time of the function

2. Using function
- Call ```send_msg()``` function
- ```send_msg()``` function receives message to send

## Example
1. Using decorator

    <img src="https://user-images.githubusercontent.com/47859342/212695259-cddcda37-b099-4865-927a-a05fbb6a71e4.png" width="70%">

2. Using function

    <img src="https://user-images.githubusercontent.com/47859342/212695028-fa483162-b6bc-40bd-a831-5fb85d62f2a8.png" width="70%">

