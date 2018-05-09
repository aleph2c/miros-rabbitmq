.. _management-management:

Management
==========
If you are building distributed systems within an organization, it is easy to
seed a mystery cult, with its own priesthood.  Mystery cults don't scale.

If you only have a few members of your team that understand your system, they
will have too much scarcity power, and will likely start making bad decisions.
It is hard to stay accountable to yourself or others when you are a priest. We
need other people to understand what we are doing to keep our engineering
discipline.

Code reviews won't help here; it would be like reviewing the code of a control
system without knowing anything about its theory.  The analysis becomes theatre,
your team might talk about PEP8 compliance or some other style issue, but the
design will not be improved upon because it will not be understood.

Testing won't save the day, since the search space of a statechart driven
distributed system is cosmic in its reach and this is why they are useful.  But,
if you are walking into a new organization, the test plans are an excellent
place to begin your learning.  Interview the system testers; they will provide
you with the broad strokes.

Everyone on your team should understand how the dynamics work; if this isn't the
case, your system will not scale.  The maintenance programmers will add
incremental 'improvements,' that break the architecture and fragilize your
product.

We are talking about knowledge here.  Your working production code generates
knowledge, but the management of a team should provide time and funds for that
knowledge to be captured into useful documentation, and more importantly confirm
that the members of your group understand it.

I have often seen non-technical managers drive design efforts without making any
resources available for the system knowledge to be captured.  Non-Technical
managers have a superpower; they don't know anything.  If things can be
explained to them, they can understand enough to take the measure of what their
group knows.  They can use themselves as a measuring stick.  A manager governs
the process, and the intention of the process should be for the entire group to
learn together. 

If you are designing distributed systems, or managing teams that are doing it,
the organization in which you work, should be part of your design.

.. _management-useful-documenation:

Useful Documentation
--------------------
Statechart based distributed systems do not stay put.  The smallest change in
the code could wipe out pages and pages of carefully written documentation.  So,
it might be a waste of effort to write everything down.

A picture is worth a thousand words; but what type of picture do you use to draw
a distributed statechart?  The Harel formalism captured in UML drawings are
pretty good; since a change in the code usually doesn't require much work to
change their diagrams.  But, it is hard to mentally render the system dynamics
from a set of distributed statechart pictures.

Most people can understand distributed dynamics from looking at sequence
diagrams; they are intuitive.  Unfortunately, they, like writing, are incredibly
fragile to design changes.  I have lost weeks of time trying to update my
sequence diagrams to match simple adjustments to a distributed statechart.

To address the fragility of the sequence diagram, I wrote the sequence tool.  It
takes trace instrumentation from multiple nodes and renders it into ASCII
sequence diagrams so that they can be dropped into the code as comments, or
written into markdown, sphinx, or where ever you put your information.  Instead
of spending time drawing a custom picture, you select your trace instrumentation
and use the tool to make it draw a picture for you:

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/GQRh5Bd91O8" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>

The sequence tool does not understand your design; you will have to add your
information to the picture by numbering the signal events.  Under the diagram,
you can write what each number signifies and describe how the node interactions
work.  These sequence diagrams quickly become very big and unwieldy.  They will
not be able to explain everything, and they don't have to.  Your system is
captured in the Harel Statechart pictures.

UML class diagrams are probably the thing that killed UML.  They duplicate a lot
of functionality provided by IDEs or tag-based systems.  They emphasize classes
over objects, and they are fragile to design changes.  There is a myriad of
different arrows that are used differently in different situations.  These are
the tools of priests.  But, they can provide context, they can be useful for
describing how you have adjusted a based NetworkedFactory or
NetworkedActiveObject class to match your design specification.

Nobody understands UML; UML has contradictions in its specification.  If it were
understood, its authors would have removed the inconsistencies before it was
released.  So don't worry about being entirely faithful to UML as a formal
system; it is impossible.  Use the good parts; use the diagrams as sketches.
Ensure that new team members understand what your pictures mean.

You will be fighting your drawing tools.  Since UML became undead, not a lot of
work has been done to improve the tooling around it.  Free tools can be used to
avoid Vendor lock-in.  I use UMLet.  It allows you to build your own templates
and you can use it on all operating systems.  It has a command line program that
can be used to export their drawings into SVG and PDF formats.

As for where to keep your documents, I vote that you keep them as close as plain
text and in your revision control system.  Add a simple build process to publish
them to an internal web server.  Avoid confluence or any other technology that
wants to put their business between your team and your information.  HTML works
just fine.

Videos.  It is easy to take a video; so use them to capture your system
dynamics.  They catch tremendous amounts of information, and they are cheap and
easy to make.

.. _management-what-to-do-about-neo:

What to do about Neo
--------------------



