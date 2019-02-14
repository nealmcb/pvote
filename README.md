Pvote 1.0 beta
==============

Ka-Ping Yee, <ping@zesty.ca>

Please see http://pvote.org/ for more detailed information about Pvote.


What is Pvote?
--------------

Pvote is prototype software for electronic voting machines.

Pvote is not a complete voting system. It is just the software program
that interacts with the voter. Other necessary functions, such as voter
registration, ballot preparation, and canvassing, are not part of Pvote. 

Pvote is designed so it could be the core user interface component for
many kinds of voting machines, such as an electronic ballot marker or
printer, a DRE (direct recording electronic) machine with or without a
paper trail, or a system with end-to-end cryptographic verification.
Any electronic voting system needs a reliable and auditable way to
present the ballot to the voter. Pvote aims to fulfill that need.


Running Pvote
-------------

Pvote runs on Linux, Mac OS X, and Windows systems.  To run it, you need:

  - Python (available at http://python.org/)
  - Pygame (available at http://pygame.org/)
  - a ballot definition file (available at http://pvote.org/code/)

The ballot definition should be a file called "ballot".  Put this file
in the same directory as the Pvote code.  Then, in this directory, run
"demo.py".  On Linux or Mac OS X you can execute "demo.py" directly
from a shell prompt.  On Windows, double-click on the icon for "demo.py"
to launch Python.

Press Esc to quit the program.

"demo.py" is a slightly modified version of "main.py", the actual main
module of Pvote that was reviewed in the security review.  It contains
two small changes: (a) the Esc key quits the program (in Pvote, there
is no way to quit, by design) and (b) the "rb" option is supplied to
the "open" command to prevent Windows from mangling linefeed characters
in the ballot definition file.


Security Review
---------------

This version of Pvote, 1.0 beta, is exactly the source code that was
reviewed in a three-day intensive software security review at UC Berkeley,
held on March 29, 30, and 31, 2007.  The design, implementation, security
claims, and arguments for correctness are set out in the Pvote Software
Review Assurance Document presented to the review team.  This assurance
document is available as UC Berkeley EECS Technical Report 2007-40, at:

    http://www.eecs.berkeley.edu/Pubs/TechRpts/2007/EECS-2007-40.html

The reviewers did not find any bugs in this source code, but they did
find an error in the assurance document. 

More information on the review is available at http://pvote.org/.
