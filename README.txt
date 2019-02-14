Prerendered Voting User Interface
Release 0.4, 2006-07-31

This software implements an electronic voting machine.  The design
of the software separates the definition of the user interface from
the program running in the voting machine.  The ballot definition
file contains prerendered images of the screen and interface elements.
Since the voting machine only needs to paste these images onto the
screen, its software can be made simpler and easier to verify.

The prototype is written in Python and consists of five small parts:

    run            13 - handles incoming touch events
    Ballot.py     126 - loads and verifies the ballot definition file
    Navigator.py   94 - keeps track of voter selections
    Recorder.py    38 - stores votes tamper-evidently and anonymously
    Video.py       22 - pastes prerendered images onto the display

    Total         293 lines (ignoring blank lines and comments)

Included here is a sample ballot definition file called "ballot".
To run the prototype:

    1.  Ensure that you have Python 2.3 and Pygame installed.
        (They run on many computing platforms and are available
        from http://python.org/ and http://pygame.org/.)

    2.  Type "./run" or otherwise execute the file "run".

    3.  Use the mouse pointer to operate the simulated touchscreen.

See http://zesty.ca/voting/ for more information.


-- Ka-Ping Yee (ping@zesty.ca)
