.. _management-describing-your-system:

Documenting
===========
Statechart based distributed systems do not stay put.  The smallest change in
the code could wipe out pages and pages of carefully written documentation.  It
might not be worth your time to write everything down.

Draw pictures instead.  But what type of picture do you use to draw a
distributed statechart?  Start with a map and sketch it out using the Harel
formalism.  The Harel formalism captured in UML drawings are pretty good; since
a change in the code usually doesn't require much work to change its diagram.
Eighty percent of our mental processing is dedicated to understanding visuals;
so draw pictures.

But, it is hard to mentally render the system dynamics from a set of distributed
statechart pictures.

Most people can understand distributed dynamics from looking at sequence
diagrams; they are intuitive.  Unfortunately, they, like writing, are incredibly
fragile to design changes.  I have lost weeks of time trying to update my
sequence diagrams to match simple adjustments to a distributed system.  What a
waste of time.

To address the fragility of the sequence diagram, I wrote the sequence tool.  It
takes trace instrumentation from multiple nodes and renders it into ASCII
sequence diagrams so that they can be dropped into the code as comments, or
written into markdown, sphinx, or where ever you put your information.  Instead
of spending time drawing a custom sequence diagram, you select your trace
instrumentation and use the tool to make it draw a picture for you.

This means that you have to write working code before you can document it.  If
you are like me, your first map will be wrong and your code's behavior as seen
using it's instrumentation will show you where you have made mistakes.  Once you
have iterated a few times, your map will be closer to what you intended to build
and you will have some useful multi-node trace information that you can use to
draw a sequence diagram for you.

Here is a video of some capture trace instrumentation being turned into a
sequence diagram describing a distributed interaction:

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/GQRh5Bd91O8" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>

The sequence tool does not understand your design; you will have to add your
information to the picture by numbering the signal events.  Under this numbered
diagram, you can write what each number signifies and describe how the node
interactions work.  These sequence diagrams quickly become very big and
unwieldy.  They will not be able to explain everything, and they don't have to.
Your system is captured in the Harel Statechart pictures.

UML has a PR problem.  As a brand people associate it to the waterfall software
design process, they associate it to the slow machinations of old tech companies
like IBM.  They associate it to failure.  And it was probably the UML class
diagrams that did the most to kill the UML brand.  They duplicate a lot of
functionality provided by IDEs or tag-based systems.  They emphasize classes
over objects, and they are fragile to design changes.  There is a myriad of
different arrows that are used differently in different situations.  But, they
can provide context, they can be useful for describing how you have adjusted a
based NetworkedFactory or NetworkedActiveObject class to match your design
specification.

Nobody understands UML; UML has contradictions in its specification.  If it were
understood, its authors would have removed the inconsistencies before it was
released.  So don't worry about being entirely faithful to UML as a formal
system; you can't, it is impossible.  Use the good parts; use the diagrams as
sketches.  Ensure that new team members understand what your pictures mean.

You will be fighting your drawing tools.  Since UML became undead, not a lot of
work has been done to improve the tooling around it.  Free tools can be used to
avoid Vendor lock-in.  I use UMLet.  It allows you to build your own templates
and you can use it on all operating systems.  It has a command line program that
can be used to export its drawings into SVG and PDF formats.  If you need to
collaborate with others on a diagram, use umletino.

As for where to keep your documents, I vote that you keep them as close as plain
text as possible and in your revision control system.  Add a simple build
process to publish them to an internal web server.  Avoid confluence or any
other technology that wants to put their business between you and your
information.  HTML works just fine.

Videos.  It is easy to take a video; so use them to capture your system
dynamics.  They catch tremendous amounts of information, and they are cheap and
easy to make.

In summary.  Accept that the system will never be fully described.  Focus on the
economics of describing enough of it so that you can see what is going on, and
you can describe it to another person.  Use free tools, constantly redraw your
statecharts as they get closer to what you want.  Use the working code on
multiple nodes to output instrumentation logs, then use these logs with the
sequence tool to draw sequence diagrams.  These rendered sequence diagrams are
cheap to make and will do a lot to describe the key parts of your multi-node
dynamics.

.. raw:: html

  <a class="reference internal" href="reflection.html#reflection"><span class="std std-ref">prev</span></a>,
  <a class="reference internal" href="index.html#top"><span class="std std-ref">top</span></a>,
  <span class="inactive-link">next</span>
