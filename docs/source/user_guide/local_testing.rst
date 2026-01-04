Local Testing Mode
==================

NoxRunner provides a local testing mode for offline development and testing without requiring a running backend service.

Overview
--------

Local testing mode uses a local sandbox backend that:

- Creates temporary directories in ``/tmp/noxrunner_sandbox_*``
- Executes commands in your local environment
- Provides all the same API as the remote backend
- Includes security restrictions to prevent dangerous operations

.. warning::

   **Important**: Local testing mode executes commands in your local environment. 
   This can cause data loss or security risks if used improperly. 
   Use only for testing purposes!

Enabling Local Testing
----------------------

As a Library
~~~~~~~~~~~~

.. code-block:: python

   from noxrunner import NoxRunnerClient

   # Enable local testing mode
   client = NoxRunnerClient(local_test=True)

   # Use normally
   client.create_sandbox("my-session")
   result = client.exec("my-session", ["echo", "Hello"])
   client.delete_sandbox("my-session")

As a CLI Tool
~~~~~~~~~~~~~

Use the ``--local-test`` flag:

.. code-block:: bash

   noxrunner --local-test create my-session
   noxrunner --local-test exec my-session echo "Hello"
   noxrunner --local-test delete my-session

Security Features
-----------------

The local sandbox backend includes several security features:

Path Sanitization
~~~~~~~~~~~~~~~~~

All file paths are sanitized to prevent path traversal attacks. 
Paths outside the sandbox directory are automatically redirected to the workspace.

Command Validation
~~~~~~~~~~~~~~~~~

Dangerous commands are blocked:

- ``rm``, ``rmdir``, ``unlink``: File deletion
- ``sudo``, ``su``: Privilege escalation
- ``chmod``, ``chown``: Permission changes
- ``mount``, ``umount``: Filesystem operations

Sandbox Isolation
~~~~~~~~~~~~~~~~~

All operations are restricted to the sandbox directory. 
Commands cannot access files outside the sandbox.

Warnings
--------

The local backend prints warnings:

- On initialization: Warns about local mode
- On every exec: Warns about command execution

These warnings are printed to stderr with colored output.

Limitations
-----------

- No true isolation (runs in local environment)
- Limited security compared to containerized backends
- Not suitable for production use
- Some backend features may not be fully implemented

Best Practices
--------------

1. **Use for Testing Only**: Never use local mode in production
2. **Clean Up**: Always delete sandboxes when done
3. **Unique Session IDs**: Use unique IDs to avoid conflicts
4. **Check Warnings**: Pay attention to warning messages
5. **Test Carefully**: Verify behavior matches remote backend

