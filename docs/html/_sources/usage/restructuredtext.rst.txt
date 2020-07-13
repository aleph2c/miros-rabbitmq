================
reStructuredText
================

| See `Sphinx's reStructuredText Guide`_
| See `Docutils authoritative reStructuredText User Documentation`_.


Inline markup
=============

.. code-block:: rst

  *one asterisk* for emphasis
  **two asterisks** for strong
  ``two backticks`` for code

*one asterisk* for emphasis

**two asterisks** for strong

``two backticks`` for code

Use backslashes to escape characters, for example, the spaces around an emphasized word:

.. code-block:: rst

  doc/\ *your_filename*\ .rst

doc/\ *your_filename*\ .rst

Linking
-------

.. code-block:: rst

  External reference_
  External `reference phrase`_
  External `reference with embedded url <https://docutils.sourceforge.io/rst.html>`_
  `Internal reference`_

External reference_

External `reference phrase`_

External `reference with embedded url <https://docutils.sourceforge.io/rst.html>`_

`Internal reference`_

Section titles, footnotes, and citations automatically generate hyperlink targets (the title text or footnote/citation label is used as the hyperlink name). These are called *implicit links*. For example, here is an implicit link to `Grid tables`_.

.. code-block:: rst

  Footnote reference [1]_, and another [2]_
  Citation reference [CIT2002]_

Footnote reference [1]_, and another [2]_

Citation reference [CIT2002]_

Full urls are automatically made into references, for example, https://docutils.sourceforge.io/rst.html

You can reference arbitrary locations in another document within your documentation using labels. If you place a label directly before a section title, you can link to it like so:

To create a label before a section heading:

::

  .. _my-section-label:

  Section Heading
  ---------------

To link to a label that has been placed before a section heading:

::

  For example see :ref:`my-section-label`.

For example see :ref:`my-section-label`.

Note that the heading text will be inserted into the link.

Labels that *aren’t* placed before a section title can still be referenced to, but you must give the link an explicit title, using this syntax: ``:ref:`Link title <label-name>```.

To create a label *not* placed before a section heading:

::

  .. _my-non-section-label:

To link to a label *not* placed before a section heading:

::

  For example see: :ref:`my reference <my-non-section-label>`

For example see: :ref:`my reference <my-non-section-label>`.

Substitutions
-------------

Substitution reference: text that is wrapped in pipes like: ``|13ds|`` can be swapped out with text or images when the document is rendered for example: ``.. |13ds| replace:: 13 Down Software Inc`` or ``.. |13ds| image:: logo.png``. This bit is often set in the `rst_epilog` or `rst_prolog` in `conf.py` file so that the substitution is applied site-wide.

|13ds|


Section Structure
=================

It would appear that you can use any nonalphanumeric character to indicate a heading. All you have to do is underline (or over and underline) to at least the same length as the text. If the second heading uses a different character, it will be treated as a subheading and so on.

The python convention is this:

- ``#`` with overline, for parts
- ``*`` with overline, for chapters
- ``=``, for sections
- ``-``, for subsections
- ``^``, for subsubsections
- ``"``, for paragraphs

I don't really get what their distinction is between parts, chapters and sections and why there's one for paragraphs but... the point is, select a pattern and stick to it. For example, in this page I've used:

::

  ================
  Main Title: <h1>
  ================

  Section: <h2>
  =============

  Subsection: <h3>
  ----------------


Lists
=====

Unordered
---------

- bullet lists uses one asterisk
- also hyphens work
- the list will have the class ``<ul class="simple">``

  * nested lists must be indented 2 spaces
  * and have a space before and after

- continuation of the main list


Ordered
-------

#. use numbers and a dot for numbered lists
#. or use ``#.`` for auto-numbering lists
#. the list will have the class ``<ol class="arabic simple">``


Definition Lists
----------------

Definition list term (can only be one line)
   Definition of the term, which must be indented

   and can even consist of multiple paragraphs

next term
   Description.


Field lists
-----------
This is just a definition list with ``class="field-list simple"``. The term and definition elements have alternating classes ``field-odd`` and ``field-even``.

:what:
    Field lists map field names to field bodies, like database records. They are often part of an extension syntax.

:how:
    The field marker is a colon, the field name, and a colon.

    The field body may contain one or more body elements, indented relative to the field marker.

:Authors:
    Jessica Rush,
    Scott Volk

:Version: 1.0
:Last update: |today|


Option Lists
------------
This is just a definition list with ``class="option-list"``

Option lists are two-column lists of command-line options and descriptions, documenting a program's options. There should be at least two spaces between the option and its description. For example:

-a            command-line option a
-b file       options can have long...

              ...multiline descriptions
--long        options can be long
--input=file  long options can also have arguments
/V            DOS/VMS-style options too

This just creats a definition list with ``<kbd>`` elements.


Blocks
======

Paragraphs
----------

Paragraphs are simply chunks of text separated by one or more blank lines.


Blockquotes
-----------

Blockquotes are created by indenting a paragraph.

  For example this text will be wrapped in a ``<p>`` element, inside a ``<div>`` which will then be inside the ``<blockquote>``


Indented Literal Blocks
-----------------------

Indented literal blocks are a type of pre-formatted code block. A ``::`` paragraph starts a literal block. The following indented lines will be part of the block. Whitespace, newlines, blank lines, and markup is preserved.

::

  def myfunction1(num1, num2):
    '''This is an example ok'''
    print(num1 * num2)

By default, syntax highlighting for these literal blocks is python but this can be changed on a document-wide basis using the `highlight directive`_.

For example:

.. highlight:: rst

::

  .. highlight:: rst

This language will used on all literal blocks until the next highlight directive is encountered. If you prefer to specify syntax highlighting on a block-by-block basis, use the `code block directive`_.

Syntax highlighting is provided by Pygments_. There are a number if different styles to choose from. You can set your preferred style in your ``conf.py``. Pygments also provides `instructions on creating your own style`_.


Code Blocks
-----------

To use the `code block directive`_ to indicate javascript syntax, replace ``::`` with ``.. code-block:: javascript``. The language can be `any lexer alias supported by Pygments`_. Most common ones you can pretty much guess but note there are useful ones like ``pycon`` and ``pytb`` for python console and python traceback code.

Code blocks can have a number options set, for example:

::

  .. code-block:: javascript
    :linenos:
    :lineno-start: 5
    :emphasize-lines: 2,5
    :caption: app/static/example.js
    :name: example-js

``linenos`` will turn on line numbering
``lineno-start`` starts the line numbering at a given number
``emphasize-lines`` highlights given lines
``caption`` adds a visible caption
``name``  creates a name label for linking

The options above will output like this:

.. code-block:: javascript
  :linenos:
  :lineno-start: 5
  :emphasize-lines: 2,5
  :caption: app/static/example.js
  :name: example-js

  function logAmount(amt) {
    console.log(amt.toFixed(2));
    console.log('Testing really long line because this makes a table and ...');
  }

  let amount = 9.9888;

  logAmount(amount * 2);  // 19.98


Quoted Literal Blocks
---------------------

Quoted literal blocks are similar to indented literal blocks in that they start with a ``::`` paragraph. They are unindented contiguous blocks of text where each line begins with the same non-alphanumeric printable 7-bit ASCII character, for example, ``>`` or ``$`` or ``|``. A blank line ends a quoted literal block. Note that the quoting characters are kept in the processed document.

::

$ The following are all valid quoting characters:
$
$ ! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \ ] ^ _ ` { | } ~


Line Blocks
-----------

A pipe ``|`` at the start of a line is said to be a way of preserving line breaks.

| In reality, it just replaces the <p> with a div: ``<div class="line-block">``
| And wraps each line in its own div: ``<div class="line">``


Doctest blocks
--------------

Doctest blocks are meant to be used to output python interpreter examples. You start a block with ``>>>`` and it ends at the first empty line.

>>> print('This is a doctest block.')
This is a doctest block.


Comments
--------

Arbitrary indented text that follows the *explicit markup start* (``..``) will be processed as a comment element. For example:

.. code-block:: rst

  .. This is a hidden comment!

.. This is a hidden comment!


Admonitions
-----------

.. admonition:: generic

  This is a generic admonition. (class="admonition-generic admonition")

.. attention::

  This is an attention. (class="admonition attention")

.. caution::

  This is a caution. (class="admonition caution")

.. danger::

  This is a danger. (class="admonition danger")

.. error::

  This is an error. (class="admonition error")

.. hint::

  This is a hint. (class="admonition hint")

.. important::

  This is important. (class="admonition important")

.. note::

  This is a note. (class="admonition note")

.. seealso::

  This is a seealso. (class="admonition seealso")

.. tip::

  This is a tip. (class="admonition tip")

.. warning::

  This is a warning! (class="admonition warning")


Tables
======

There are two ways of creating tables in rst, grid tables and simple tables. Grid tables are ASCII art-like and super cumbersome to to produce but are nice because they allow for arbitrary cell contents. Simple tables are simpler to create but obviously more limited. You can also create "list tables" using the list-table directive.


Grid tables
-----------

Grid tables are made up of the characters ``-``, ``=``, ``|``, and ``+``. The hyphen ``-`` is used for horizontal lines (row separators). The equals sign ``=`` may be used to indicate optional header rows. The vertical bar ``|`` is used for vertical lines (column separators). The plus sign ``+`` is used for intersections of horizontal and vertical lines. For example:

+-----------------+-----------------+-----------------+
| Header 1        | Header 2        | Header 3        |
+=================+=================+=================+
| body row 1      | column 2        | column 3        |
+-----------------+-----------------+-----------------+
| body row 2      | Cells may span columns.           |
+-----------------+-----------------+-----------------+
| body row 3      | Cells may       | - cells can     |
+-----------------+ span rows.      | - contain other |
| body row 4      |                 | - elements.     |
+-----------------+-----------------+-----------------+


Simple tables
-------------

Simple tables are compact and easier to type. These are best suited to basic data tables. Cell contents are typically single paragraphs, although you can add some other body elements. Simple tables allow multi-line rows (in all but the first column) and column spans, but not row spans.

Simple tables are described with horizontal borders made up of ``=`` and ``-`` characters. The equals sign ``=`` is used for top and bottom table borders, and to indicate optional header. The hyphen ``-`` is used to indicate column spans in a single row by underlining the joined columns, and may optionally be used to explicitly and/or visually separate rows. For example:

========  ========  ========
Header 1  Header 2  Header 3
========  ========  ========
row 1     col 2     col 3
row 2     col 2     col 3
row 3     column span

          - with a list
          - inside
          - the cell
--------  ------------------
row 4     col 2     col 3
========  ========  ========


List tables
-----------

The `list-table directive`_ is useful when dealing with long simple lists of data. This example only has two columns but you can have as many as you want. One of the nice things about using this directive is that you have access to options like alignment and column width.

.. list-table::
   :widths: 25 80
   :header-rows: 1
   :align: left

   * - label
     - description
   * - Feature:
     - a new feature added
   * - Fix:
     - a bug Fix
   * - Docs:
     - Documentation changes only
   * - Style:
     - formatting, whitespace changes only
   * - Refactor:
     - code changes than neither fix a bug or add a feature
   * - Perf:
     - code changes that improve performance
   * - Test:
     - adding tests
   * - Update:
     - changes related to updated external libraries/dependencies


Explicit markup
===============

Explicit markup blocks are used for:

- floating elements like footnotes,
- elements with no direct paper-document representation like comments or hyperlink targets,
- directives that require specialized processing

Explicit markup starts with two periods and whitespace.

.. Links & Footnotes

.. [1] Footnote 1 content...

.. [2] Footnote 2 content...

.. [CIT2002] Citation content...

.. _`Sphinx's reStructuredText Guide`: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#

.. _`Docutils authoritative reStructuredText User Documentation`: https://docutils.sourceforge.io/rst.html

.. _reference: https://docutils.sourceforge.io/docs/user/rst/quickref.html#hyperlink-targets

.. _`reference phrase`: https://docutils.sourceforge.io/docs/user/rst/quickref.html#hyperlink-targets

.. _`highlight directive`: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-highlight

.. _`code block directive`: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block

.. _Pygments: https://pygments.org/demo/#try

.. _any lexer alias supported by Pygments: https://pygments.org/docs/lexers/

.. _`instructions on creating your own style`: https://pygments.org/docs/styles/

.. _`Docutils full list of directives`: https://docutils.sourceforge.io/docs/ref/rst/directives.html

.. _`Sphinx's full list of directives`: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html

.. _`list-table directive`: https://docutils.sourceforge.io/docs/ref/rst/directives.html#list-table

.. _`common options`: https://docutils.sourceforge.io/docs/ref/rst/directives.html#common-options

.. _`Internal reference`:

Internal reference test content...


Directives
==========

Directives are a general-purpose extension mechanism of reST, a way of adding support for new constructs without adding new syntax. Some common ones are:

- `Code Blocks`_
- `List tables`_
- `Admonitions`_
- `Images`_
- `Figures`_
- `Containers`_
- `Epigraphs`_
- `Meta`_
- `Raw HTML`_
- `Contents`_
- `Glossary`_
- `Include`_
- `Literal Include`_
- `Role`_

Note that with many directives, there is a main option that is placed on the same line as the name of the directive. For examples, with code blocks—the language, with images—the file path, with links—the URI. For example:

::

  .. code-block:: javascript
    :linenos:

  .. image:: ../_static/logo.svg
    :width: 25px

  .. _`github`: https://github.com/


.. note:: There are two `common options`_ that can be added to almost any directive: ``class:`` and ``name:``. Class is used to set a "class" attribute value on the element generated by the directive. Name is used set the "name" attribute which can then be used as an internal hyperlink target.

| See `Docutils full list of directives`_.
| See `Sphinx's full list of directives`_.


Images
------

Possible options include:

.. code-block:: rst

  .. image:: ../_static/logo.svg
    :width: 25px
    :height: 25px
    :alt: alternate text
    :target: `reStructuredText`_
    :scale: 50
    :align: left
    :name: logo
    :class: scale-to-fit


Example:

.. image:: ../_static/logo.svg
  :alt: alternate text
  :target: `reStructuredText`_
  :class: scale-to-fit

Note that images are often placed as substitutions, for example:

.. code-block:: rst

  |diagram|

  a bunch of content

  .. |diagram| image:: ../_static/diagram1.svg
    :alt: alternate text
    :class: diagram-full


Figures
-------

A figure directive coverts to an html ``<div>``, ``<img>`` and ``<p>``.

.. code-block:: rst

  .. figure:: ../_static/logo.svg
     :alt: alternate text
     :width: 100px

     This is the caption of the figure.

Example:

.. figure:: ../_static/logo.svg
   :alt: alternate text
   :width: 100px

   This is the caption of the figure.


Containers
----------

The container directive will surround its contents with a generic block-level "container" element. For example this reST:

.. code-block:: rst

  .. container:: special

     This paragraph will be wrapped in its own container.

...will output this in *make html*:

.. code-block:: html

  <div class="special docutils container">
    <p>This paragraph will be wrapped in its own container.</p>
  </div>


Epigraphs
---------

An epigraph is just a blockquote with optional attribution line.

This rst:

.. code-block:: rst

  .. epigraph::

     No matter where you go, there you are.

     -- Buckaroo Banzai

Results in this html:

.. code-block:: html

  <blockquote class="epigraph">
    <div>
      <p>No matter where you go, there you are.</p>
      <p class="attribution">—Buckaroo Banzai</p>
    </div>
  </blockquote>

Like so:

.. epigraph::

   No matter where you go, there you are.

   -- Buckaroo Banzai


Meta
----

The meta directive is used to specify html metadata stored.

For example this rst:

.. meta::
   :description: The reStructuredText plaintext markup language
   :keywords: plaintext, markup language

.. code-block:: rst

   .. meta::
      :description: The reStructuredText plaintext markup language
      :keywords: plaintext, markup language

Outputs as:

.. code-block:: html

  <meta name="description" content="The reStructuredText plaintext markup language">
  <meta name="keywords" content="plaintext, markup language">


Raw HTML
--------

The raw directive indicates non-reStructuredText data that is to be passed untouched to the Writer. For example:

.. code-block:: rst

  .. raw:: html

    <p><input placeholder="testing raw"><p>

Outputs:

.. raw:: html

  <p><input placeholder="testing raw"><p>


Contents
--------

The contents directive is used to generate a table of contents for the current topic (page).

It looks like this:

::

  .. contents::

It can take one optional argument, a title:

::

  .. contents:: On This Page

Note that if a title is not provided, the default "Contents" will be used.

There are also a number of possible options:

::

  .. contents:: On This Page
     :depth: 2
     :local:
     :backlinks: none
     :class: page-toc

- ``:depth:`` – the number of section levels that are included
- ``:local:`` – will only include subsections of the section in which the directive is placed
- ``:backlinks:`` – value can be set to "entry", "top" or "none". By default, the directive generates links from section headers back to the table of contents.
- ``:class:`` – adds a class attribute to the outer container.

.. contents:: On This Page
   :backlinks: none
   :depth: 2

Glossary
--------

todo


Include
-------

todo


Literal Include
---------------

todo


Role
----

The 'role' directive dynamically creates a custom interpreted text role and registers it with the parser. Basically what that means is you can create a custom role which has a set of instructions, then apply that to any text in your document.

How it works is, first you define the role by giving it a name. Typically you'd put this at the start of your document.

.. code-block:: rst

  .. role:: highlight


Then you'd add the instructions (i.e. what do you want the role to do?):

.. code-block:: rst

  .. role:: highlight
     :class: hightlight-text


Then apply that role to some text:

.. code-block:: rst

  .. role:: highlight
     :class: hightlight-text

  Testing :highlight:`my role that adds a class`.

The html output would look like this:

.. code-block:: html

  <p>Testing <span class="text-hightlight">my role that adds a class</span>.</p>

For example:

.. role:: highlight
   :class: text-hightlight

Testing :highlight:`my role that adds a class`.

Other
=====

Four or more repeated punctuation characters creates an html "transition marker" which in html translates to an ``<hr class="docutils">`` element.

----

These really shouldn't be used to begin or end a section or document. It is the semantic intent that these be used when there is a thematic break from one paragraph to the next. ok
