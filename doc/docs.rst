.. _management-describing-your-system:

Documenting
===========

.. epigraph::

  *Now is the time to understand more, so we fear less.*

  -- Marie Curie

This section is a collection of my opinions about how to describe your distributed
system.

Statechart based distributed systems do not stay put.  The smallest change in the code
could wipe out pages and pages of your carefully written documentation.  It might not be
worth your time to write everything down.

I'll explore this idea using a topographical map as an analogy.  A topographical map describes
the landscape from a bird's eye view, where each contour line is drawn at a specific elevation.
To see what this landscape would look like while on the ground, you would need to make a
topographical projection.

The diagram below [#]_ describes how a topographical projection is made from a topographical
map.  In the bottom box of the picture we see a topographical map of a volcano.  In the
top box we see it's topographical projection, or what it would look like while walking toward
it from the south:

.. image:: _static/topographical_projection.gif
    :align: center

If you were to approach this same mountain from the west instead, you would need to make
a new topographical projection.  In fact you could make many many different
topographical projections of this one diagram, each describing a different directional
approach to the same mountain. 

Your statechart and it's diagram are like the topographical map.  They both contain many
many different approaches or stories.  A specific feature of your statechart program is
like a vantage point from the ground.  To describe how it works you would send a few
events to the chart and watch how it reacts using the trace instrumentation.  Then, if
you were to write or draw a sequence diagram for this feature, you would be making
something like a topographical projection.

.. image:: _static/volcano_exploding.jpg
   :align: center

The volcano explodes [#]_.  It has a new shape, which we have bravely surveyed
and our topographical map has been updated.  But now every one of our carefully
drawn topographical projections needs to be redone, because every approach to
the volcano will look different than it did before.  Likewise, if you make a
slight adjustment to your statechart, all of the sequence diagrams and the
writing used to describe your features need to be re-drawn and re-written.

A distributed set of statecharts is like a bunch of different topographical maps
working together.  I think that the analogy breaks down at this point, but the
consequences hold.  If your design requires a set of interactions between
concurrently running statecharts, you need to be able to create a set of
sequence diagrams and some writing to describe how their dynamics work together
to manifest your system's design feature.  These diagrams and the writings
around them are very fragile to change.

Before we leave the topographical map analogy, let's think about the utility of
the topographical projection.  Anyone can understand it, because this is what
you see when you are walking around on the ground.  The bird's eye view,
topographical map needs to be explained, some people understand right away and
others don't, but there is a level of abstraction between it's model of the
world and the observer's understanding of what it is trying to reveal.  This
holds true with the statechart.  Statechart designers will have no problem
viewing the dynamics of a chart, but other members of their team might have a
harder time seeing what is going on. Everyone understands a sequence diagram.

The engineering features for a complex system are always changing.  Our
volcano's are always blowing up, re-growing and blowing up again.  But, it is OK
to spend your time carefully drawing your HSM diagrams, since they match the
code.  They pack a tremendous amount of complexity into a small space.  You get
good bang for your buck.  But, use tooling to auto-generate the sequence
diagrams then write about them sparingly.  Keep it quick and dirty, American
style. 差不多.  Don't waste your time drawing beautiful projections.

I wrote the sequence tool to draw your sequence diagrams for you.  It takes trace
instrumentation from multiple nodes and renders it into ASCII sequence diagrams so that
they can be dropped into the code as comments, or written into markdown, sphinx, or
where ever you put your information.  Instead of spending time drawing a custom sequence
diagram, you select your trace instrumentation and let the tool draw a picture for you.

This means that you have to write working code before you can document it with words.
If you are like me, your first map will be wrong and your code's behavior as seen
through it's instrumentation will show you where you have made mistakes.  Once you have
iterated a few times, your map will be closer to what you intended to build and you will
have some useful multi-node trace information that you can use to draw a sequence
diagram for you.

Here is a video of some capture trace instrumentation being turned into a sequence
diagram describing a distributed interaction:

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/GQRh5Bd91O8" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>

The sequence tool does not understand your design; you will have to add your
information to the picture by numbering the event signal names.  Under this
numbered diagram, you can write what each number signifies and describe how the
various node interactions work.  These sequence diagrams quickly become very big
and unwieldy.  They will not be able to explain everything, and they don't have
to.  Your Harel Statechart pictures capture your system.

Another thing worth noting is that UML has a PR problem.  As a brand people
associate it with the 90's waterfall software management process, they associate
it with the slow machinations of old tech companies like IBM.  They associate it
with failure.  It was probably the UML class diagrams that did the most to harm
the UML brand.  They emphasize classes over objects, and they are fragile to
design changes.  There is a myriad of different arrows that are used differently
in different situations.  But, they can provide context, they can be useful for
describing how you have adjusted a base NetworkedFactory or
NetworkedActiveObject class to match your design specification.

Nobody understands UML; UML has contradictions in its specification.  If it were
understood, its authors would have removed the inconsistencies before it was
released.  So don't worry about being entirely faithful to UML as a formal
system; you can't, it is impossible.  Use the good parts of UML; use its
diagrams as sketches, not as the software itself.  Ensure that new team members
understand what your pictures mean;  don't build a priesthood.

You will be fighting your drawing tools.  Since UML became undead, not a lot of
work has been done to improve the tooling around it.  But there are still some
free tools you can be used to avoid Vendor lock-in.  I use UMLet.  It allows you
to build your own templates, based on theirs and you can use it on all operating
systems because UMLet is written in Java.  It's fast and ugly, so you don't fall
in love with your pictures.  It has a command line program that can be used to
export its drawings into SVG and PDF formats.

As for where to keep your documents, I vote that you keep them as close as plain
text as possible and in your revision control system.  Add a simple build
process to publish them to an internal web server.  Avoid confluence or any
other technology that wants to put their business between you and your
information.  HTML works just fine.

Videos!  It is easy to take a video; so use them to capture your system
dynamics.  They catch tremendous amounts of information, and they are cheap and
easy to make.

In summary.  Accept that the system will never be adequately described.  Focus
on the economics of describing enough of it so that you can see what is going
on, and you can relate it to another person.  Use free tools, constantly redraw
your statecharts as they get closer to what you want.  Use the working code on
multiple nodes to output instrumentation logs, then use these logs with the
sequence tool to draw sequence diagrams.

.. raw:: html

  <a class="reference internal" href="reflection.html#reflection"><span class="std std-ref">prev</span></a>,
  <a class="reference internal" href="index.html#top"><span class="std std-ref">top</span></a>,
  <a class="reference internal" href="deployment.html"><span class="std std-ref">next</span></a>

.. [#] The topographical map and it's projection were taken from an online `course about how to read maps <https://courses.lumenlearning.com/geo/chapter/reading-maps/>`_.
.. [#] The above photo was taken by `Fredrik Holm <https://www.flickr.com/photos/fredrikholm>`_ 

