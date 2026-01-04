Introduction
============

What is NoxRunner?
------------------

**NoxRunner** is a Python client library for interacting with NoxRunner-compatible sandbox execution backends. 
It provides a simple, unified interface for managing isolated execution environments where you can safely run code.

Key Features
------------

- **Zero Dependencies**: Uses only Python standard library - no external dependencies required
- **Complete API Coverage**: Supports all NoxRunner backend endpoints
- **Friendly CLI**: Command-line interface with colored output and interactive shell
- **Local Testing Mode**: Offline testing with local sandbox backend
- **Type Hints**: Full type support for better IDE experience
- **Well Documented**: Comprehensive documentation and examples

Use Cases
---------

NoxRunner is ideal for:

- **Code Execution Services**: Run user-submitted code in isolated environments
- **CI/CD Pipelines**: Execute build scripts and tests in sandboxed containers
- **Educational Platforms**: Provide safe code execution for learning
- **Testing Frameworks**: Test code in isolated environments
- **Development Tools**: Local testing and development workflows

Architecture
------------

NoxRunner follows a client-server architecture:

.. mermaid::
   :align: center

   graph LR
       A[Python Client] -->|HTTP API| B[NoxRunner Backend]
       B --> C[Sandbox Environment]
       C --> D[Container/Pod]

The client communicates with a backend service that manages sandbox execution environments. 
The backend can be implemented using various technologies:

- Kubernetes-based sandbox managers
- Docker-based execution backends
- VM-based sandbox systems
- Custom implementations following the specification

Backend Compatibility
---------------------

NoxRunner is designed to work with any backend that implements the 
:doc:`NoxRunner Backend Specification <../SPECS>`. This specification defines:

- RESTful HTTP API endpoints
- Request/response formats
- Error handling
- Session management
- File operations

See the `Backend Specification <../../SPECS.md>`_ for complete specification details.

Next Steps
----------

- Read the :doc:`quickstart` guide to get started
- Explore the :doc:`tutorial/index` for step-by-step examples
- Check out the :doc:`api_reference/index` for complete API documentation

