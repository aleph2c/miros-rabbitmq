How it Works (Design Re-write in Progress)
==========================================


.. _how_it_works2-the-cache-file-chart:

The Cache File Chart
--------------------
The network discovery process is expensive, so we will cache its results to a
JSON file.

The cache will persist beyond the life of the program that wrote it.  When the
next program runs, it will read the cache, determine if it is young enough to be
useful, and if so, it will skip the expensive network discovery process.

We use the JSON format since we will be transmitting this cache to other hosts
and JSON has become the standard format for transmitting data.

But there could be thousands of processes trying to read and write to this cache
file at the same time.  To address this concern, we wrap this file access into
an active object which will check if the file is writable before trying to read
or write from it.  If the file is writable, the statechart will determine that
no other program is using the file.

.. image:: _static/miros_rabbitmq_cache_file_chart.svg
    :target: _static/miros_rabbitmq_cache_file_chart.pdf
    :align: center

The design was intended to be built within another statechart and to start
itself upon being constructed.  The CacheFileChart subscribes to the
``CACHE_FILE_WRITE`` and the ``CACHE_FILE_READ`` events.  If any other part of the
program wants to see what is in the cache, they would post a ``CACHE_FILE_READ``.
The CacheFileChart will send a ``CACHE`` event with the contents of the cache and
whether the cache has been expired.

If any other statechart would like to write the cache, they would place the
contents of the write into a dict as the payload of the ``CACHE_FILE_WRITE``.

Internally the ``CACHE_FILE_READ`` and ``CACHE_FILE_WRITE`` public events are turned
into the ``file_read`` and ``file_write`` events.  When the state chart sees that such
an event is posted it will try to enter the file_read or file_write states.
Such transitions can be blocked if the file is not writable (set by the OS).  In
the case that the event is blocked, the statechart re-posts the same event to
itself at a future time, then stops running.  The re-posting time is a random
number between 0.001 and a timeout.  This timeout parameter increases for each
re-posting failure, to a maximum value of 5 seconds.

If a ``file_read`` or ``file_write`` event succeeds to transition past the file access
state, it will lock the file by making it un-writable.  This global state, put
onto the file by the operating system will make the file exclusive to this
program.  When the file is read or written, the CacheFileChart will post either
a read_successful or write_successful event to itself.  This will cause an exit
signal to occur on the file_accessed state, which will make the file writable.
Other programs will now have the ability to access the same file when their
deferred ``file_read`` or ``file_write`` events fire.

The internal code within the file_read and file_write states was taken from
various stack overflow articles describing how to safely read and write a file
in a very short period of time, in an environment where many other programs are
trying to do the same thing.

.. _how_it_works2-producescoutchart:

ProduceScoutChart
-----------------

