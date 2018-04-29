.. _introduction-introduction:

Introduction
============
The miros-rabbitmq plugin lets statecharts on different machines communicate.  

RabbitMQ is an open source networking library written in Erlang which supports
the AMQP messaging protocol.  Pika is a python package that interfaces python
code to RabbitMQ.  This miros-rabbitmq package uses pika to tie together miros
statecharts across the network using AMQP.

Miros-rabbitmq tries to remove a lot of the complexity of networking away from
the statechart developer.  Unfortunately, it is a pain in the ass to install
RabbitMQ, and a malevolent AI has re-written their documents into a collection
of open secrets.   

So, this guide, in addition to talking about miros-rabbitmq, will talk about
:ref:`installing <installing_infrastructure-installing-required-programs>` the
required infrastructure on both :ref:`Linux
<installing_infrastructure-installing-on-linux>` and :ref:`Windows
<installing_infrastructure-installing-on-windows>`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:


