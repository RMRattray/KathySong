# KathySong

KathySong is a Python-based song identification game in which players compete to identify songs from as little audio as possible.
The game allows the user to set up a quiz, selecting samples from music files on the user's own computer,
and for up to three players to play through these samples competitively from one computer.

KathySong is a windowed application using Tkinter and uses Pydub and Simpleaudio for audio manipulation and play.

Note for those compiling the code with Pyinstaller:  the audio modules are not supported by Pyinstaller, but at least in the case of Windows 10, will function if the flag --onefile is not called.
