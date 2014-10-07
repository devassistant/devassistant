How It Works/PingPong Protocol Reference
========================================

The DevAssistant PingPong protocol is a simple protocol that DevAssistant (Server) and
PingPong script (Client) use to communicate through a pipe. It's designed to be as simple
and portable as possible.

The overall idea of PingPong is:

* Server invokes Client script as a subprocess and attaches to its stdin/stdout/stderr,
  creating a pipe.
* Client waits for Server to initiate the communication.
* Server sends the first message, initiating the communication.
* Server and Client communicate through the pipe.
* At one point, the Client is done and the subprocess exits. Server gathers its output
  data and acts up on them in some way.

Right now, only Python implementation of the protocol is available. In future, we'll be
aiming to implement the Client side (used in PingPong scripts) in other dynamic languages
(or you can do it yourself using the reference below and let us know!)

.. _why_pingpong:

Why PingPong?
-------------

The "PingPong" name comes from the similarity to table tennis. There are two players,
Server (DevAssistant) and Client (PingPong script). The Server serves (sends the first
message), Client receives it and responds to server, Server receives the message and
responds again to Client, ...

How Does PingPong Integrate With DSL?
-------------------------------------

In terms of integration with DevAssistant Yaml DSL, PingPong is just another
:ref:`command runner <pingpong_command_ref>` that computes something and then returns
a result. This means that you can mix it up arbitrarily with other DSL commands or even
run several PingPong scripts in one assistant.

Reference
---------

This part describes DevAssistant PingPong Protocol (**DAPP**) version **2**. There is a
`reference Python implementation <https://github.com/devassistant/dapp>`_,
called ``dapp``, which you can examine into detail. Note that the reference implementation
implements both Server and Client side. If you're considering implementing DAPP
in another scripting language, you'll only need to implement Client side.

Errors
~~~~~~

Throughout this reference, there are certain situations marked as *"being an error"*.
These situations usually mean that a (fatal) error was encountered in message format.
The side getting the error should terminate immediately, possibly running cleanup code first.

Message Format
~~~~~~~~~~~~~~

These points are general rules that apply to all messages, both sent from Server to Client
(S->C) and Client to Server (C->S).

- Currently, sending random binary data is not supported, everything has to be valid
  UTF-8 encoded string. Not being able to decode is an error.
- Each message starts with string ``START`` and ends with string ``STOP``. These have to be
  on separate lines.
- Any non-empty line between previous ``STOP`` and following ``START`` is an error.
- The lines between ``START`` and ``STOP`` must a valid Yaml mapping, otherwise it is an error.
- Every message has to contain ``msg_number``, ``msg_type`` and ``dapp_protocol_version``.
- ``dapp_protocol_version`` must be an integer specifying the DAPP protocol version.
  Other side using a different protocol version is an error.
- ``msg_number`` must be a unique integer identifying the message during a PingPong script run.
  Sequence of message numbers must be increasing; both sides use the same sequence (e.g. Server
  sends message ``1``, client then has to send message with number no lower than ``2``, then
  Server has to send a message with number no lower than the number of message sent by client
  etc). This rule has one exception, confirmation messages (``msg_type`` is ``msg_received``)
  have the same number as the message that they're confirming. More on the confirmation
  messages below.
- If ``msg_type`` is different than ``msg_received``, message must contain ``ctxt``. Valid
  message types are listed below.
- ``ctxt`` has to be a Yaml DSL context (e.g. mapping of variable names to their values).
  In every message (except confirmation message), the whole context has to be passed and the
  receiving communication side must update its copy of the context.

Message Types and Content
~~~~~~~~~~~~~~~~~~~~~~~~~

- Both Client and Server send ``msg_received`` messages to confirm messages received from
  the other communicating side.
- Server sends these messages:

  - ``run`` - This message must always be the first message in the whole communication,
    Server sends it to tell Client to start and pass the initial context. This message
    shouldn't contain any special data.
  - ``command_result`` - Reports result of a command that Client previously invoked. Must
    contain ``lres`` and ``res`` values, these two represent results of the command
    (see :ref:`command_ref` for details).
  - ``command_exception`` - Sent if the command called by Client raised an exception. Must
    contain ``exception`` value, which is a string representation of the exception.
  - ``no_such_command`` - Sent if Server (DevAssistant) doesn't know how to execute
    the sent command. Doesn't contain any extra data.

- Client sends these messages:

  - ``call_command`` - Client calls a command. Must contain ``command_type`` and
    ``command_input``, as specified in :ref:`command_ref`.
  - ``finished`` - Client ended successfully. Must contain ``lres`` and ``res`` values.
    These must be the same types as return values of DevAssistant commands (again, see
    :ref:`command_ref`).
  - ``failed`` - Client failed. Must contain ``fail_desc`` with the description of
    the failure.

If ``run`` from Server to Client isn't the first message and ``finished`` or ``failed``
isn't the last message from Client to Server, it is an error.

Example Communication
~~~~~~~~~~~~~~~~~~~~~

To illustrate better how the protocol works, here is a simple example of valid message sequence.
We're assuming that the Server has already started the Client and Client is now waiting to
for Server to initiate the communication.

Note that all the communication is shown as an already decoded Unicode, but in fact it's sent
as UTF-8 through the pipe.

Server initiates communication by sending ``run`` message::

   START
   dapp_protocol_version: 2
   msg_type: run
   msg_number: 1
   ctxt:
     name: user_input_name
     some_list_variable: [foo, bar, baz]
   STOP

Client confirms that it got the message::

   START
   dapp_protocol_version: 2
   msg_type: msg_received
   msg_number: 1
   STOP

And imediatelly after that it starts to actually do something. At certain points, it needs to
call back to Server (DevAssistant) to carry out some tasks implemented in DevAssistant itself.
Note, that while computing, the Client process has done some modifications to the context::

   START
   dapp_protocol_version: 2
   msg_type: call_command
   msg_number: 2
   ctxt:
     name: user_input_name
     some_dict_variable: {foo: a, bar: b, baz: c}
   command_type: log_i
   command_input: This will get logged by DevAssistant to either GUI or console.
   STOP

The Server (DevAssistant) first confirms receiving the message by sending ``msg_received``::

   START
   dapp_protocol_version: 2
   msg_type: msg_received
   msg_number: 2
   STOP

Then the server actually runs the command and sends a message with result to Client::

   START
   dapp_protocol_version: 2
   msg_type: command_result
   msg_number: 3
   ctxt:
     name: user_input_name
     some_dict_variable: {foo: a, bar: b, baz: c}
   lres: True
   res: This will get logged by DevAssistant to either GUI or console.
   STOP

(Note that for the ``log_i`` command, the ``res`` result is actually equal to the input; this
is usually not the case, of course).

Again, Client confirms receiving the message::

   START
   dapp_protocol_version: 2
   msg_type: msg_received
   msg_number: 3
   STOP

And then Client continues to compute. Since this is a simple example, the Client doesn't call any
more commands, but it could call as many as it'd like. The client is now finished and prepared
to exit, so it sends a ``finished`` message::

   START
   dapp_protocol_version: 2
   msg_type: command_result
   msg_number: 4
   ctxt:
     name: user_input_name
     some_dict_variable: {foo: a, bar: b, baz: c}
     another_variable: some_var
   lres: True
   res: 42
   STOP

Server sends one last confirmation message to Client::

   START
   dapp_protocol_version: 2
   msg_type: msg_received
   msg_number: 4
   STOP

And everything is done. The Client can safely exit and Server can do anything it wishes with
the result.
