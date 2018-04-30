  *Wars teach us not to love our enemies, but to hate our allies*

  -- W. L George

.. _introduction-introduction:

Introduction
============
The miros-rabbitmq plugin lets `miros
<https://aleph2c.github.io/miros/index.html>`_ statecharts on different machines
communicate.  By networking statecharts you can build distributed systems, IOT
frameworks or Botnets.

RabbitMQ is an open source networking library written in Erlang which supports
the AMQP messaging protocol.  Pika is a python package that interfaces Python
code to RabbitMQ.  This miros-rabbitmq package uses pika to tie together miros
statecharts across the network using AMQP.

Miros-rabbitmq tries to remove a lot of the complexity of networking away from
the statechart developer.  Unfortunately, installing RabbitMQ is not trivial,
and their documents are written as a collection of open secrets.

So, this guide, in addition to talking about miros-rabbitmq, will talk about
:ref:`installing <installing_infrastructure-installing-required-programs>` the
required infrastructure on both :ref:`Linux
<installing_infrastructure-installing-on-linux>` (using automation) and :ref:`Windows
<installing_infrastructure-installing-on-windows>`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:


