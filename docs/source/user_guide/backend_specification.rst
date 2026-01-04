Backend Specification
=====================

NoxRunner is designed to work with any backend that implements the NoxRunner Backend Specification.

See the `Backend Specification <../../SPECS.md>`_ for the complete specification.

Key Points
----------

- RESTful HTTP API
- JSON request/response format
- Standard HTTP status codes
- Session-based sandbox management
- TTL (Time To Live) support

Implementing a Backend
----------------------

To implement a NoxRunner-compatible backend:

1. Read the :doc:`../../SPECS` document
2. Implement all required endpoints
3. Follow the request/response formats
4. Handle errors appropriately
5. Test with the NoxRunner client

The specification is designed to be flexible and can be implemented using:

- Kubernetes
- Docker
- Virtual machines
- Custom containerization systems

