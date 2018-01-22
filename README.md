# HomeAgents

## Description
HomeAgents is a protocol (and an implementation) to stream interface to an Arduino screen (TFT 2.2 inchs for example) over TCP/IP.
User interaction are sended back to the server.

The Arduino, with an ethernet shield and a touchscreen, acts like a lightweight client.

For streaming, pictures have to be compressed.
Becasue of the Arduino low calculation power, we cannot use standards comrpession formats (jpeg, etc).

This protocol try differents "parts" of compression that are easy to uncompress :
- Encode color in RGB565
- RLE
- Color palet

More compression techics could be implemented.

## File descrptions

To work on the server, a "fake client" was created, wich simulate a touchscreen.

You can run "server.py", then launch "client.py".
