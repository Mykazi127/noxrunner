Getting Started Tutorial
========================

This tutorial will guide you through the basics of using NoxRunner.

Step 1: Installation
--------------------

Install NoxRunner:

.. code-block:: bash

   pip install noxrunner

Step 2: Create a Client
-----------------------

.. code-block:: python

   from noxrunner import NoxRunnerClient

   # Create client (replace with your backend URL)
   client = NoxRunnerClient("http://127.0.0.1:8080")

Step 3: Create a Sandbox
------------------------

.. code-block:: python

   session_id = "tutorial-session"
   result = client.create_sandbox(session_id, ttl_seconds=600)
   print(f"Created sandbox: {result['podName']}")

Step 4: Wait for Ready
----------------------

.. code-block:: python

   if client.wait_for_pod_ready(session_id, timeout=60):
       print("Sandbox is ready!")
   else:
       print("Sandbox did not become ready")

Step 5: Execute Commands
-------------------------

.. code-block:: python

   result = client.exec(session_id, ["python3", "--version"])
   print(f"Exit code: {result['exitCode']}")
   print(f"Output: {result['stdout']}")

Step 6: Upload Files
--------------------

.. code-block:: python

   files = {
       "hello.py": "print('Hello from NoxRunner!')"
   }
   client.upload_files(session_id, files)

Step 7: Download Files
----------------------

.. code-block:: python

   tar_data = client.download_files(session_id)
   # Extract or process tar_data as needed

Step 8: Clean Up
----------------

.. code-block:: python

   client.delete_sandbox(session_id)

Complete Example
----------------

.. code-block:: python

   from noxrunner import NoxRunnerClient

   client = NoxRunnerClient("http://127.0.0.1:8080")
   session_id = "example-session"

   try:
       # Create sandbox
       client.create_sandbox(session_id)
       client.wait_for_pod_ready(session_id)

       # Upload and run a script
       client.upload_files(session_id, {
           "script.py": "print('Hello, World!')"
       })
       
       result = client.exec(session_id, ["python3", "script.py"])
       print(result["stdout"])

   finally:
       # Always clean up
       client.delete_sandbox(session_id)

Next Steps
----------

- Read :doc:`basic_usage` for more examples
- Check :doc:`advanced_usage` for advanced features

