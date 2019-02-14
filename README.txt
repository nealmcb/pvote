Prerendered Voting User Interface
Release 0.5.1 (Ptouch), 2007-11-22

This software implements an electronic voting machine.  The design
of the software separates the definition of the user interface from
the program running in the voting machine.  The ballot definition
file contains prerendered images of the screen and interface elements.
Since the voting machine only needs to paste these images onto the
screen, its software can be made simpler and easier to verify.

The prototype is written in Python and consists of five small parts:

    main.py        13 - handles incoming touch events
    Ballot.py     126 - loads and verifies the ballot definition file
    Navigator.py   92 - keeps track of voter selections
    Recorder.py    38 - stores votes tamper-evidently and anonymously
    Video.py       22 - pastes prerendered images onto the display

    Total         291 lines (ignoring blank lines and comments)

Included here is a sample ballot definition file called "ballot" and
an empty vote storage file called "votes".  To run the prototype:

    1.  Ensure that you have Python 2.3 and Pygame installed.
        (They run on many computing platforms and are available
        from http://python.org/ and http://pygame.org/.)

    2.  Type "python main.py" or otherwise execute the file "main.py".

    3.  Use the mouse pointer to operate the simulated touchscreen.

See http://pvote.org/ for more information.


-- Ka-Ping Yee (ping@zesty.ca)
