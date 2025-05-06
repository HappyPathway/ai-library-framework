# Python Dependencies

This document provides an overview of the Python dependencies used in this project.

## Table of Contents

- [Async](#category-async): Asynchronous programming tools
- [Other](#category-other): Miscellaneous libraries
- [Ai](#category-ai): AI and machine learning libraries for model interaction and processing
- [Web](#category-web): Web services, APIs, and networking
- [Dev](#category-dev): Development tools and utilities
- [Cloud](#category-cloud): Cloud service integration libraries
- [Core](#category-core): Core Python functionality extensions
- [Testing](#category-testing): Testing and quality assurance
- [Data](#category-data): Data processing, storage, and serialization

## <a name='category-async'></a> Async Packages

Asynchronous programming tools

### amqp (5.3.1)

Low-level AMQP client for Python (fork of amqplib).

AgentRunResult(output='The provided documentation excerpt, "Please enable JavaScript to proceed," does not contain any information about the Python package \'amqp\'. Therefore, I cannot summarize its purpose, features, or use cases based on this text.')

**Links:** [Website](https://pypi.org/project/amqp/)

---

### anyio (4.9.0)

High level compatibility layer for multiple asynchronous event loop implementations

AgentRunResult(output="AnyIO is an asynchronous networking and concurrency library that enables code to run unmodified on either `asyncio` or `trio` backends. Key features include trio-like structured concurrency (task groups), cancellation, timeouts, synchronization primitives, and asynchronous file I/O. It's commonly used for building backend-agnostic I/O-bound applications and libraries that require robust concurrent operations.")

**Links:** [Website](https://pypi.org/project/anyio/) | [Documentation](https://anyio.readthedocs.io/en/latest/)

---

### async-timeout (5.0.1)

Timeout context manager for asyncio programs

AgentRunResult(output='The provided documentation excerpt ("Please enable JavaScript to proceed.") does not contain any information about the \'async-timeout\' Python package. Therefore, I cannot summarize its purpose, features, or common use cases based on this text.')

**Links:** [Website](https://pypi.org/project/async-timeout/) | [GitHub](https://github.com/aio-libs/async-timeout/actions)

---

### celery (5.5.2)

Distributed Task Queue.

AgentRunResult(output='Based on the excerpt, Celery is a distributed task queue system designed to process large volumes of messages asynchronously. Its key features include real-time processing and task scheduling, making it suitable for offloading long-running operations, handling background work, and executing periodic tasks in a distributed environment.')

**Links:** [Website](https://pypi.org/project/celery/) | [Documentation](https://docs.celeryq.dev/en/stable/)

---

### pyzmq (25.1.2)

Python bindings for 0MQ

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pyzmq/) | [Documentation](https://pyzmq.readthedocs.org)

---

## <a name='category-other'></a> Other Packages

Miscellaneous libraries

### annotated-types (0.7.0)

Reusable constraint types to use with typing.Annotated

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/annotated-types/)

---

### argcomplete (3.6.2)

Bash tab completion for argparse

AgentRunResult(output="Argcomplete is a Python package that enables bash/zsh tab completion for command-line arguments defined using Python's `argparse` module. Key features include the `argcomplete.autocomplete(parser)` function to register an argparse parser, support for various completers like `ChoicesCompleter`, `DirectoriesCompleter`, and `FilesCompleter`, and the ability to activate global completion. It is commonly used to enhance the user experience of Python command-line interface (CLI) applications by making argument input faster and less error-prone.")

**Links:** [Website](https://pypi.org/project/argcomplete/) | [Documentation](https://kislyuk.github.io/argcomplete)

---

### astroid (3.3.9)

An abstract syntax tree for Python with inference support.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/astroid/)

---

### billiard (4.2.1)

Python multiprocessing fork with improvements and bugfixes

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/billiard/)

---

### botocore (1.38.8)

Low-level, data-driven core of boto 3.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/botocore/)

---

### certifi (2025.4.26)

Python package for providing Mozilla's CA Bundle.

AgentRunResult(output="Certifi is a Python package that supplies Mozilla's carefully curated collection of Root Certificates (CA Bundle). Its key function is to enable Python applications to validate the trustworthiness of SSL certificates and verify TLS host identities by providing a reliable, portable root of trust, though it doesn't allow modification of the bundle.")

**Links:** [Website](https://pypi.org/project/certifi/)

---

### cffi (1.17.1)

Foreign Function Interface for Python calling C code.

AgentRunResult(output='cffi is a Python package that enables interaction with C code, allowing Python to call C functions and work with C data structures. It primarily')

**Links:** [Website](https://pypi.org/project/cffi/) | [Documentation](http://cffi.readthedocs.org/)

---

### charset-normalizer (3.4.2)

The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.

AgentRunResult(output='Charset-normalizer is a Python library that helps read text from unknown character encodings by finding an encoding that best transposes the content to Unicode, rather than trying to determine the original encoding. Key features include support')

**Links:** [Website](https://pypi.org/project/charset-normalizer/) | [Documentation](https://charset-normalizer.readthedocs.io/)

---

### cohere (5.15.0)

AgentRunResult(output='The provided documentation excerpt, "Please enable JavaScript to proceed," does not contain any information about the Python package \'cohere\'. Therefore, it\'s not possible to summarize what the package does, its key features, or its common use cases based solely on this text.')

**Links:** [Website](https://pypi.org/project/cohere/)

---

### colorama (0.4.6)

Cross-platform colored terminal text.

AgentRunResult(output='Colorama is a Python package that enables cross-platform colored terminal text and cursor positioning by making ANSI escape sequences work correctly, especially on MS Windows. Its key capability is translating these sequences for Windows, allowing developers to create visually richer command-line interfaces that behave consistently across different operating systems.')

**Links:** [Website](https://pypi.org/project/colorama/)

---

### cryptography (44.0.3)

cryptography is a package which provides cryptographic recipes and primitives to Python developers.

AgentRunResult(output="The 'cryptography' Python package provides developers with cryptographic recipes (high-level operations) and primitives (low-level building blocks). It is a production-stable library, supporting various Python versions and operating systems, commonly used for implementing security features within Python applications.")

**Links:** [Website](https://pypi.org/project/cryptography/)

---

### deprecated (1.2.18)

Python @deprecated decorator to deprecate old python classes, functions or methods.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/Deprecated/) | [Documentation](https://deprecated.readthedocs.io/en/latest/)

---

### dill (0.4.0)

serialize all of Python

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/dill/) | [Documentation](http://dill.rtfd.io)

---

### distro (1.9.0)

Distro - an OS platform information API

AgentRunResult(output="The 'distro' Python package provides an API to retrieve operating system platform information, specifically for Linux and various BSD distributions. It is primarily used by developers and system administrators to identify the OS, enabling them to write platform-aware code or perform OS-dependent system tasks.")

**Links:** [Website](https://pypi.org/project/distro/)

---

### eval_type_backport (0.2.2)

Like `typing._eval_type`, but lets older Python versions use newer typing features.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/eval-type-backport/)

---

### executing (2.2.0)

Get the currently executing AST node of a frame, and other information

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/executing/)

---

### fastavro (1.10.0)

Fast read/write of AVRO files

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/fastavro/)

---

### filelock (3.18.0)

A platform independent file lock.

AgentRunResult(output="The 'filelock' package provides a platform-independent file locking mechanism for inter-process communication, using a separate `.lock` file to signal that a resource or working directory is in use. Key features include exclusive, recursive locks, support for timeouts, and non-blocking acquisition. It's commonly used to coordinate access to shared resources, such as ensuring only one process writes to a file while others can read it, thus preventing race conditions.")

**Links:** [Website](https://pypi.org/project/filelock/) | [Documentation](https://py-filelock.readthedocs.io)

---

### fsspec (2025.3.2)

File-system specification

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/fsspec/) | [Documentation](https://filesystem-spec.readthedocs.io/en/latest/)

---

### gitdb (4.0.12)

Git Object Database

AgentRunResult(output="GitDB is a pure-Python library that provides an interface to Git's object database, allowing developers to read and potentially write Git objects like blobs, trees, and commits. Its key capability is offering low-level, programmatic access to Git's internal data structures without external dependencies. This is commonly used by developers building custom Git tooling, analysis scripts, or applications that need to interact directly with repository data.")

**Links:** [Website](https://pypi.org/project/gitdb/)

---

### gitpython (3.1.42)

GitPython is a Python library used to interact with Git repositories

AgentRunResult(output='GitPython is a Python library that allows developers to interact with Git repositories. It offers both high-level (like git-porcelain) and low-level (like git-plumbing) interfaces, making it suitable for programmatically managing repositories, automating Git workflows, or building custom Git tooling.')

**Links:** [Website](https://pypi.org/project/GitPython/)

---

### google-api-core (2.24.2)

Google API client core library

**Links:** [Website](https://pypi.org/project/google-api-core/) | [Documentation](https://googleapis.dev/python/google-api-core/latest/) | [GitHub](https://github.com/googleapis/python-api-core)

---

### google-api-python-client (2.167.0)

Google API Client Library for Python

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/google-api-python-client/)

---

### google-auth (2.39.0)

Google Authentication Library

AgentRunResult(output='The `google-auth` Python package simplifies server-to-server authentication for accessing Google APIs. Key features include handling various Google authentication mechanisms and offering optional extras for specific needs like different HTTP client integrations or enterprise certificate support. It is primarily used by developers whose applications need to securely authenticate with Google services programmatically.')

**Links:** [Website](https://pypi.org/project/google-auth/)

---

### google-auth-httplib2 (0.2.0)

Google Authentication Library: httplib2 transport

AgentRunResult(output='The `google-auth-httplib2` Python package provides an `httplib2` transport layer for the `google-auth` library. Its key capability and primary use case is to assist developers in migrating existing applications that use `oauth2client` (which often relies on `httplib2`) to the newer `google-auth` library, despite `httplib2` being discouraged due to issues like lack of thread safety.')

**Links:** [Website](https://pypi.org/project/google-auth-httplib2/)

---

### google-crc32c (1.7.1)

A python wrapper of the C library 'Google CRC32C'

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/google-crc32c/)

---

### google-resumable-media (2.7.2)

Utilities for Google Media Downloads and Resumable Uploads

AgentRunResult(output='The `google-resumable-media` Python package provides utilities for handling Google media downloads and, crucially, resumable uploads, allowing large file transfers to be paused and resumed')

**Links:** [Website](https://pypi.org/project/google-resumable-media/)

---

### googleapis-common-protos (1.70.0)

Common protobufs used in Google APIs

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/googleapis-common-protos/) | [GitHub](https://github.com/googleapis/google-cloud-python/tree/main/packages/googleapis-common-protos)

---

### greenlet (3.2.1)

Lightweight in-process concurrent programming

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/greenlet/) | [Documentation](https://greenlet.readthedocs.io/)

---

### griffe (1.7.3)

Signatures for entire Python programs. Extract the structure, the frame, the skeleton of your project, to generate API documentation or find breaking changes in your API.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/griffe/) | [Documentation](https://mkdocstrings.github.io/griffe) | [GitHub](https://github.com/mkdocstrings/griffe)

---

### groq (0.24.0)

The official Python library for the groq API

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/groq/) | [GitHub](https://github.com/groq/groq-python)

---

### grpc-google-iam-v1 (0.14.2)

IAM API client library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/grpc-google-iam-v1/) | [GitHub](https://github.com/googleapis/google-cloud-python)

---

### grpcio (1.72.0rc1)

HTTP/2-based RPC framework

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/grpcio/) | [Documentation](https://grpc.github.io/grpc/python)

---

### grpcio-status (1.71.0)

Status proto mapping for gRPC

AgentRunResult(output='The `grpcio-status` Python package provides the reference implementation for mapping gRPC status information (including error details) to Protocol Buffer messages. It is a production-stable package, depending on `grpcio`, used when Python gRPC applications need to define or interpret rich, structured status/error information beyond standard gRPC status codes.')

**Links:** [Website](https://pypi.org/project/grpcio-status/)

---

### h11 (0.16.0)

A pure-Python, bring-your-own-I/O implementation of HTTP/1.1

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/h11/)

---

### httpcore (1.0.9)

A minimal low-level HTTP client.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/httpcore/) | [Documentation](https://www.encode.io/httpcore)

---

### httplib2 (0.22.0)

A comprehensive HTTP client library.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/httplib2/)

---

### idna (3.10)

Internationalized Domain Names in Applications (IDNA)

AgentRunResult(output='The provided documentation excerpt ("Please enable JavaScript to proceed.") does not contain any information about the Python package \'idna\'.\n\nHowever, based on general knowledge, the Python \'idna\' package implements the Internationalized Domain Names in Applications (IDNA) 2008 standard. Its key capability is to convert Unicode domain names (which can contain non-ASCII characters) into an ASCII-compatible encoding (ACE), known as Punycode, and vice-versa, which is essential for applications like web browsers or email clients to correctly handle internationalized domain names.')

**Links:** [Website](https://pypi.org/project/idna/)

---

### importlib_metadata (8.6.1)

Read metadata from Python packages

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/importlib-metadata/)

---

### iniconfig (2.1.0)

brain-dead simple config-ini parsing

AgentRunResult(output="Based on the documentation, 'iniconfig' is a small and simple Python package designed for parsing INI configuration files. Its key features include maintaining the order of sections and entries and supporting multi-line values, making it useful for developers who need a straightforward way to read settings from INI files in their applications.")

**Links:** [Website](https://pypi.org/project/iniconfig/)

---

### jiter (0.9.0)

Fast iterable JSON parser.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/jiter/)

---

### jmespath (1.0.1)

JSON Matching Expressions

AgentRunResult(output='JMESPath is a Python package that allows developers to declaratively extract specific elements from')

**Links:** [Website](https://pypi.org/project/jmespath/)

---

### kombu (5.5.3)

Messaging library for Python.

AgentRunResult(output='The provided documentation excerpt ("Please enable JavaScript to proceed.") does not')

**Links:** [Website](https://pypi.org/project/kombu/)

---

### markdown-it-py (3.0.0)

Python port of markdown-it. Markdown parsing, done right!

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/markdown-it-py/) | [Documentation](https://markdown-it-py.readthedocs.io)

---

### mccabe (0.7.0)

McCabe checker, plugin for flake8

AgentRunResult(output="The 'mccabe' package is a Python tool, functioning as a plugin for flake8, that measures the McCabe cyclomatic complexity of code. Its key capability is to identify overly complex code sections, commonly used by developers to improve code quality and maintainability as part of their software development and quality assurance processes.")

**Links:** [Website](https://pypi.org/project/mccabe/)

---

### mcp (1.7.1)

Model Context Protocol SDK

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/mcp/) | [GitHub](https://github.com/modelcontextprotocol/python-sdk)

---

### mdurl (0.1.2)

Markdown URL utilities

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/mdurl/)

---

### nodeenv (1.9.1)

Node.js virtual environment builder

AgentRunResult(output="Nodeenv is a Python tool that creates isolated Node.js virtual environments, ensuring each environment has its own installation directories and doesn't share libraries with others. Key features include this isolation and the ability to integrate with Python's `virtualenv`, making it useful for managing project-specific Node.js dependencies and versions, especially in development scenarios involving both Node.js and Python.")

**Links:** [Website](https://pypi.org/project/nodeenv/)

---

### opentelemetry-api (1.32.1)

OpenTelemetry Python API

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/opentelemetry-api/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

### opentelemetry-exporter-otlp-proto-common (1.32.1)

OpenTelemetry Protobuf encoding

AgentRunResult(output='The `opentelemetry-exporter-otlp-proto-common` package provides shared functionality for encoding OpenTelemetry data into the Protobuf format. Its key capability is to offer a common Protobuf encoding mechanism, primarily used as an internal dependency by other OpenTelemetry exporters like `opentelemetry-exporter-otlp-proto-grpc` and `opentelemetry-exporter-otlp-proto')

**Links:** [Website](https://pypi.org/project/opentelemetry-exporter-otlp-proto-common/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

### opentelemetry-exporter-otlp-proto-http (1.32.1)

OpenTelemetry Collector Protobuf over HTTP Exporter

AgentRunResult(output='The `opentelemetry-exporter-otlp-proto-http` Python package enables applications to export telemetry data to an OpenTelemetry Collector. It achieves this by using the OpenTelemetry Protocol (OTLP) with Protobuf payloads transported over HTTP, primarily for developers integrating Python applications with OpenTelemetry.')

**Links:** [Website](https://pypi.org/project/opentelemetry-exporter-otlp-proto-http/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

### opentelemetry-instrumentation (0.53b1)

Instrumentation Tools & Auto Instrumentation for OpenTelemetry Python

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/opentelemetry-instrumentation/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python-contrib)

---

### opentelemetry-proto (1.32.1)

OpenTelemetry Python Proto

AgentRunResult(output='The `opentelemetry-proto` package provides the Python-generated code for the OpenTelemetry protobuf data model, based on a specific version of the `opentelemetry-proto` specifications. Its key capability is to offer these pre-generated Python')

**Links:** [Website](https://pypi.org/project/opentelemetry-proto/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

### opentelemetry-sdk (1.32.1)

OpenTelemetry Python SDK

AgentRunResult(output='The `opentelemetry-sdk` is the official Python Software Development Kit for the OpenTelemetry framework, enabling developers to instrument their Python applications. It is a production-stable package, primarily used by developers to integrate OpenTelemetry for collecting telemetry data from their services.')

**Links:** [Website](https://pypi.org/project/opentelemetry-sdk/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

### opentelemetry-semantic-conventions (0.53b1)

OpenTelemetry Semantic Conventions

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/opentelemetry-semantic-conventions/) | [GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

### packaging (25.0)

Core utilities for Python packages

AgentRunResult(output='The `packaging` library provides reusable core utilities for implementing Python packaging interoperability specifications. Key features include offering a single, correct implementation for standards like PEP 440 (versioning) and PEP 425 (compatibility tags). It is commonly used by other Python packaging tools to ensure consistent interpretation and handling of package metadata.')

**Links:** [Website](https://pypi.org/project/packaging/) | [Documentation](https://packaging.pypa.io/)

---

### pathspec (0.12.1)

Utility library for gitignore style pattern matching of file paths.

AgentRunResult(output="Based on the documentation excerpt, the 'pathspec' Python package is designed for matching file paths against specified patterns. It prominently features capabilities related to `.gitignore` style patterns (specifically `gitwildmatch`), making it commonly used for implementing file filtering or ignore logic similar to how Git handles `.gitignore` files.")

**Links:** [Website](https://pypi.org/project/pathspec/) | [Documentation](https://python-path-specification.readthedocs.io/en/latest/index.html)

---

### platformdirs (4.3.7)

A small Python package for determining appropriate platform-specific dirs, e.g. a `user data dir`.

AgentRunResult(output='Platformdirs is a Python library that determines platform-specific system directories for storing application files. It identifies standard locations for user-specific data (cache, config, logs, documents) and shared data across various operating systems like Android, macOS, Unix, and Windows. This is commonly used by applications to save configuration, cache, or user data in the correct, OS-idiomatic locations.')

**Links:** [Website](https://pypi.org/project/platformdirs/) | [Documentation](https://platformdirs.readthedocs.io)

---

### pluggy (1.5.0)

plugin and hook calling mechanisms for python

AgentRunResult(output='Pluggy is a Python package that provides core mechanisms for managing plugins and calling hooks, enabling extensibility in applications. It is a mature framework primarily used by developers to build extensible software development and testing tools, as seen in projects like pytest, tox, and devpi.')

**Links:** [Website](https://pypi.org/project/pluggy/)

---

### proto-plus (1.26.1)

Beautiful, Pythonic protocol buffers

**Links:** [Website](https://pypi.org/project/proto-plus/) | [Documentation](https://googleapis.dev/python/proto-plus/latest/) | [GitHub](https://github.com/googleapis/proto-plus-python)

---

### protobuf (5.29.4)

AgentRunResult(output="Based on this documentation excerpt, the 'protobuf' Python package is installable via pip and requires Python 3.9 or higher, but its specific purpose, features, and common use cases are not described. The provided information focuses on metadata like licensing (3-Clause BSD), author, and release history, which includes details about yanked versions due to issues like incorrect Python version configuration.")

**Links:** [Website](https://pypi.org/project/protobuf/)

---

### pyasn1 (0.6.1)

Pure-Python implementation of ASN.1 types and DER/BER/CER codecs (X.208)

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pyasn1/) | [Documentation](https://pyasn1.readthedocs.io)

---

### pyasn1_modules (0.4.2)

A collection of ASN.1-based protocols modules

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pyasn1-modules/)

---

### pycodestyle (2.11.1)

Python style guide checker

AgentRunResult(output="pycodestyle is a tool that checks Python code against the style conventions found in PEP 8, acting as a Python style guide checker. Its key capability is to identify deviations from PEP 8, and it's commonly used by developers to ensure their code adheres to Python's official style guide for improved readability and consistency.")

**Links:** [Website](https://pypi.org/project/pycodestyle/)

---

### pycparser (2.22)

C parser in Python

AgentRunResult(output='`pycparser` is a complete C language parser written entirely in Python, leveraging the PLY parsing library. Its key capability is to parse C code and generate an Abstract Syntax Tree (AST), making it useful as a front-end for C compilers or various C code analysis tools.')

**Links:** [Website](https://pypi.org/project/pycparser/)

---

### pyflakes (3.2.0)

passive checker of Python programs

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pyflakes/)

---

### pygithub (2.3.0)

Use the full Github API v3

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/PyGithub/) | [Documentation](https://pygithub.readthedocs.io/en/stable/)

---

### pygments (2.19.1)

Pygments is a syntax highlighting package written in Python.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/Pygments/) | [Documentation](https://pygments.org/docs)

---

### pyjwt (2.10.1)

JSON Web Token implementation in Python

AgentRunResult(output='PyJWT is a stable Python library that implements JSON Web Tokens (JWTs) according to RFC 7519. Its key capabilities include encoding (signing) and decoding (verifying) JWTs, making it commonly used for adding secure token-based authentication to Python web applications and projects.')

**Links:** [Website](https://pypi.org/project/PyJWT/)

---

### pynacl (1.5.0)

Python binding to the Networking and Cryptography (NaCl) library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/PyNaCl/)

---

### pyparsing (3.2.3)

pyparsing module - Classes and methods to define and execute parsing grammars

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pyparsing/)

---

### python-dateutil (2.9.0.post0)

Extensions to the standard Python datetime module

AgentRunResult(output="The `python-dateutil` package offers powerful extensions to Python's standard `datetime` module, enabling advanced date and time manipulations. Key features include computing relative deltas (e.g., next month, next Monday), parsing dates from almost any string format, handling complex recurrence rules (iCalendar), and comprehensive timezone support with an internal Olson database. Common use cases involve parsing diverse date strings, calculating future/recurring")

**Links:** [Website](https://pypi.org/project/python-dateutil/) | [Documentation](https://dateutil.readthedocs.io/en/stable/)

---

### python-multipart (0.0.20)

A streaming multipart parser for Python

AgentRunResult(output='Python-Multipart is a streaming multipart parser for Python, designed to efficiently process `multipart/form-data` request bodies. Its key capability is handling incoming data, such as file uploads, in chunks via callbacks without needing to store entire parts in memory. This makes it well-suited for WSGI applications that need to manage form submissions, especially')

**Links:** [Website](https://pypi.org/project/python-multipart/) | [Documentation](https://kludex.github.io/python-multipart/)

---

### rsa (4.9.1)

Pure-Python RSA implementation

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/rsa/) | [GitHub](https://github.com/sybrenstuvel/python-rsa)

---

### six (1.17.0)

Python 2 and 3 compatibility utilities

AgentRunResult(output='Six is a Python 2 and 3 compatibility library that enables developers to write code compatible with both Python 2.7+ and 3.3+. It achieves this by providing utility functions to smooth over version differences and is conveniently packaged as a single, easily integratable Python file. Its primary use case is for projects needing to maintain cross-version Python compatibility.')

**Links:** [Website](https://pypi.org/project/six/)

---

### smmap (5.0.2)

A pure Python implementation of a sliding window memory map manager

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/smmap/)

---

### sniffio (1.3.1)

Sniff out which async library your code is running under

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/sniffio/) | [Documentation](https://sniffio.readthedocs.io/)

---

### soupsieve (2.7)

A modern CSS selector implementation for Beautiful Soup.

AgentRunResult(output="Soupsieve is a modern CSS selector library specifically designed to enhance Beautiful Soup 4 by providing advanced selecting, matching, and filtering capabilities for HTML/XML content. Its key features include support for a wide range of CSS selectors (from Level 1 up to Level 4+ drafts) and the ability to be used directly via its API or as the backend for Beautiful Soup's `select` method. Common use cases involve precise element extraction from web pages for data scraping or parsing structured documents.")

**Links:** [Website](https://pypi.org/project/soupsieve/)

---

### tzdata (2025.2)

Provider of IANA time zone data

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/tzdata/) | [Documentation](https://tzdata.readthedocs.io)

---

### uritemplate (4.1.1)

Implementation of RFC 6570 URI Templates

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/uritemplate/)

---

### urllib3 (2.4.0)

HTTP library with thread-safe connection pooling, file post, and more.

AgentRunResult(output='urllib3 is a powerful, user-friendly HTTP client for Python, widely used within the Python ecosystem. It provides critical features often missing from standard libraries, such as client-side TLS/SSL verification, file uploads with multipart encoding, request retries, redirect handling, support for various content encodings (gzip, deflate, brotli, zstd), and proxy support for HTTP/SOCKS. This makes it ideal for making robust, secure, and versatile web requests.')

**Links:** [Website](https://pypi.org/project/urllib3/) | [Documentation](https://urllib3.readthedocs.io)

---

### vine (5.1.0)

Python promises.

AgentRunResult(output='Vine is a Python package that provides a special implementation of promises, designed for both promising a future value and lazy evaluation. Its key capability is that all components within a promise, such as filters, callbacks, and errbacks, can themselves be promises, making it suitable for managing complex asynchronous operations or deferred computations.')

**Links:** [Website](https://pypi.org/project/vine/)

---

### wcwidth (0.2.13)

Measures the displayed width of unicode strings in a terminal

AgentRunResult(output='The `wcwidth` Python package measures the display width of Unicode strings in a terminal, accurately accounting for characters that occupy zero, one, or two cells (like CJK characters or emoji). It provides Python equivalents of the POSIX `wcwidth()` and `wcswidth()` C functions, primarily used by CLI programs and terminal emulators to correctly format text output.')

**Links:** [Website](https://pypi.org/project/wcwidth/)

---

### wrapt (1.17.2)

Module for decorators, wrappers and monkey patching.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/wrapt/) | [Documentation](https://wrapt.readthedocs.io/)

---

### zipp (3.21.0)

Backport of pathlib-compatible object wrapper for zip files

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/zipp/)

---

## <a name='category-ai'></a> Ai Packages

AI and machine learning libraries for model interaction and processing

### anthropic (0.50.0)

The official Python library for the anthropic API

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/anthropic/) | [GitHub](https://github.com/anthropics/anthropic-sdk-python)

---

### google-ai-generativelanguage (0.6.15)

Google Ai Generativelanguage API client library

AgentRunResult(output='The')

**Links:** [Website](https://pypi.org/project/google-ai-generativelanguage/)

---

### google-generativeai (0.8.5)

Google Generative AI High level API client library and tools.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/google-generativeai/)

---

### huggingface-hub (0.30.2)

Client library to download and publish models, datasets and other repos on the huggingface.co hub

AgentRunResult(output='The `huggingface-hub` Python package is the official client library for interacting with the Hugging Face Hub, allowing users to programmatically download and publish models, datasets, and other machine learning resources. Its key capabilities include managing repository access and facilitating the sharing and discovery of assets, primarily for developers and researchers working on AI and machine learning projects.')

**Links:** [Website](https://pypi.org/project/huggingface-hub/)

---

### mistralai (1.7.0)

Python Client SDK for the Mistral AI API.

AgentRunResult(output='The `mistralai` Python package is a client SDK designed to enable developers to interact with the Mistral AI API. Key capabilities include accessing Chat Completion and Embeddings services, with features like server-sent event streaming, file uploads, and robust error handling. This allows for')

**Links:** [Website](https://pypi.org/project/mistralai/) | [GitHub](https://github.com/mistralai/client-python.git)

---

### openai (1.77.0)

The official Python library for the openai API

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/openai/) | [GitHub](https://github.com/openai/openai-python)

---

### pydantic-ai (0.1.9)

Agent Framework / shim to use Pydantic with LLMs

**Links:** [Website](https://pypi.org/project/pydantic-ai/) | [Documentation](https://ai.pydantic.dev)

---

### pydantic-ai-slim (0.1.9)

Agent Framework / shim to use Pydantic with LLMs, slim package

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pydantic-ai-slim/)

---

### pyyaml (6.0.2)

YAML parser and emitter for Python

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/PyYAML/) | [Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)

---

### tokenizers (0.21.1)

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/tokenizers/)

---

### tomlkit (0.13.2)

Style preserving TOML library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/tomlkit/) | [GitHub](https://github.com/sdispater/tomlkit)

---

### types-html5lib (1.1.11.20241018)

Typing stubs for html5lib

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/types-html5lib/) | [GitHub](https://github.com/python/typeshed)

---

## <a name='category-web'></a> Web Packages

Web services, APIs, and networking

### beautifulsoup4 (4.12.3)

Screen-scraping library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/beautifulsoup4/)

---

### fastapi (0.115.12)

FastAPI framework, high performance, easy to learn, fast to code, ready for production

**Links:** [Website](https://pypi.org/project/fastapi/) | [Documentation](https://fastapi.tiangolo.com/) | [GitHub](https://github.com/fastapi/fastapi)

---

### httpx (0.28.1)

The next generation HTTP client.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/httpx/) | [Documentation](https://www.python-httpx.org)

---

### httpx-sse (0.4.0)

Consume Server-Sent Event (SSE) messages with HTTPX.

AgentRunResult(output='The `httpx-sse` package enables Python applications to consume Server-Sent Event (SSE) messages using the HTTP')

**Links:** [Website](https://pypi.org/project/httpx-sse/)

---

### requests (2.32.3)

Python HTTP for Humans.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/requests/) | [Documentation](https://requests.readthedocs.io)

---

### sse-starlette (2.3.3)

SSE plugin for Starlette

AgentRunResult(output='The `sse-starlette` Python package is a production-stable plugin that implements the Server-Sent Events (SSE) specification for Starlette and FastAPI applications. It enables these web frameworks to push real-time, unidirectional data updates from the server to clients, making it suitable for applications requiring live notifications or streaming data feeds.')

**Links:** [Website](https://pypi.org/project/sse-starlette/)

---

### starlette (0.46.2)

The little ASGI library that shines.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/starlette/) | [Documentation](https://www.starlette.io/)

---

### types-beautifulsoup4 (4.12.0.20240229)

Typing stubs for beautifulsoup4

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/types-beautifulsoup4/) | [GitHub](https://github.com/python/typeshed)

---

### types-requests (2.31.0.20240311)

Typing stubs for requests

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/types-requests/) | [GitHub](https://github.com/python/typeshed)

---

### uvicorn (0.34.2)

The lightning-fast ASGI server.

AgentRunResult(output='Uvicorn is a "lightning-fast" ASGI web server implementation for Python, designed to run asynchronous web applications. Its key capability is providing the low-level server interface defined by the ASGI specification, making it a common tool for developers building and deploying web applications with modern async Python frameworks.')

**Links:** [Website](https://pypi.org/project/uvicorn/)

---

## <a name='category-dev'></a> Dev Packages

Development tools and utilities

### black (24.3.0)

The uncompromising code formatter.

AgentRunResult(output='Black is an uncompromising Python code formatter that automatically reformats code to a consistent style, ceding control over manual formatting minutiae. Key features include producing the smallest possible diffs for faster code reviews, ensuring deterministic output')

**Links:** [Website](https://pypi.org/project/black/) | [Documentation](https://black.readthedocs.io/) | [GitHub](https://github.com/psf/black)

---

### cachetools (5.3.3)

Extensible memoizing collections and decorators

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/cachetools/)

---

### isort (5.13.2)

A Python utility / library to sort Python imports.

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/isort/)

---

### prompt_toolkit (3.0.51)

Library for building powerful interactive command lines in Python

AgentRunResult(output='Based on the provided documentation excerpt, "Please enable JavaScript to proceed," it is not possible to determine what the \'prompt_toolkit\' package does, its key features, or common use cases. The excerpt only indicates a requirement for JavaScript to view the actual content.')

**Links:** [Website](https://pypi.org/project/prompt-toolkit/)

---

### setuptools (80.3.0)

Easily download, build, install, upgrade, and uninstall Python packages

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/setuptools/) | [Documentation](https://setuptools.pypa.io/)

---

## <a name='category-cloud'></a> Cloud Packages

Cloud service integration libraries

### boto3 (1.38.8)

The AWS SDK for Python

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/boto3/) | [Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

### google-cloud (0.34.0)

API Client library for Google Cloud

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/google-cloud/)

---

### google-cloud-core (2.4.3)

Google Cloud API client core library

AgentRunResult(output='The `google-cloud-core` package is a foundational library for Google Cloud API clients in Python, providing common helper utilities like base client classes. It is not intended for standalone use but serves as an essential dependency for other `google-cloud-*` packages, ensuring consistent functionality across different Google Cloud services accessed via Python.')

**Links:** [Website](https://pypi.org/project/google-cloud-core/)

---

### google-cloud-secret-manager (2.23.3)

Google Cloud Secret Manager API client library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/google-cloud-secret-manager/)

---

### google-cloud-storage (2.14.0)

Google Cloud Storage API client library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/google-cloud-storage/)

---

### s3transfer (0.12.0)

An Amazon S3 Transfer Manager

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/s3transfer/)

---

## <a name='category-core'></a> Core Packages

Core Python functionality extensions

### click (8.1.8)

Composable command line interface toolkit

AgentRunResult(output='Click is a Python package for creating beautiful, composable command-line interfaces (CLIs) with minimal code, aiming to make CLI development quick and fun. Key features include arbitrary nesting of commands, automatic help page generation, and support for lazy loading of subcommands. It is commonly used for building well-structured and user-friendly command-line tools in Python.')

**Links:** [Website](https://pypi.org/project/click/) | [Documentation](https://click.palletsprojects.com/)

---

### click-didyoumean (0.3.1)

Enables git-like *did-you-mean* feature in click

AgentRunResult(output='The provided documentation excerpt, "Please enable JavaScript to proceed," does not contain any information about the Python package \'click-didyoumean\'. Therefore, it\'s impossible to summarize what the package does, its key features, or common use cases based on this content.')

**Links:** [Website](https://pypi.org/project/click-didyoumean/) | [GitHub](https://github.com/click-contrib/click-didyoumean)

---

### click-plugins (1.1.1)

An extension module for click to enable registering CLI commands via setuptools entry-points.

AgentRunResult(output="'click-plugins' is a Python package that extends `click` to allow registration of external CLI commands and sub-groups using `setuptools` entry points. This enables developers to create extensible command-line interfaces where third-party plugins can add functionality (e.g., domain-specific features or commands with extra dependencies) without modifying the core application, and it gracefully handles broken or incompatible plugins.")

**Links:** [Website](https://pypi.org/project/click-plugins/)

---

### click-repl (0.3.0)

REPL plugin for Click

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/click-repl/)

---

### logfire (3.14.1)

The best Python observability tool! 🪵🔥

**Links:** [Website](https://pypi.org/project/logfire/) | [Documentation](https://logfire.pydantic.dev/docs/)

---

### logfire-api (3.14.1)

Shim for the Logfire SDK which does nothing unless Logfire is installed

AgentRunResult(output="The 'logfire-api' package is a shim that mirrors the Logfire SDK's Python API, doing nothing by default. Its key capability is to allow other packages to offer opt-in integration with Logfire; it only makes real calls if the full Logfire SDK is actually installed, thus avoiding a hard dependency for end-users.")

**Links:** [Website](https://pypi.org/project/logfire-api/)

---

### python-dotenv (1.0.0)

Read key-value pairs from a .env file and set them as environment variables

AgentRunResult(output='Python-dotenv reads key-value pairs from a `.env` file and sets them as environment variables, primarily to help manage application configurations and secrets separately from code, aligning with 12-factor app principles. Key capabilities include loading configurations without altering the global environment, parsing them as a stream, and supporting IPython integration')

**Links:** [Website](https://pypi.org/project/python-dotenv/)

---

### rich (14.0.0)

Render rich text, tables, progress bars, syntax highlighting, markdown and more to the terminal

AgentRunResult(output='Rich is a Python library for creating rich and beautiful command-line interfaces and terminal output. Its key features include styled text, tables, progress bars, syntax highlighting, pretty printing, advanced traceback formatting, and layout tools. Common use cases involve enhancing CLI applications, improving debugging output, displaying structured data effectively, and making logs more readable.')

**Links:** [Website](https://pypi.org/project/rich/) | [Documentation](https://rich.readthedocs.io/en/latest/)

---

### tqdm (4.67.1)

Fast, Extensible Progress Meter

AgentRunResult(output='Based on the documentation, `tqdm` is a Python package that provides a fast and extensible progress meter for console applications and Jupyter notebooks. Key features include displaying rate, ETA (estimated time of arrival), and its')

**Links:** [Website](https://pypi.org/project/tqdm/) | [GitHub](https://github.com/tqdm/tqdm)

---

### typing-inspection (0.4.0)

Runtime typing introspection tools

AgentRunResult(output='The `typing-inspection` package provides tools for runtime inspection of Python type annotations. Its key capability is enabling developers to examine and understand type hints programmatically during execution, which is useful for building tools or frameworks that need to dynamically react to type information.')

**Links:** [Website](https://pypi.org/project/typing-inspection/) | [Documentation](https://pydantic.github.io/typing-inspection/dev/)

---

### typing_extensions (4.13.2)

Backported and Experimental Type Hints for Python 3.8+

AgentRunResult(output="The `typing_extensions` package complements Python's standard `typing` module, primarily enabling the use of new type system features (e.g., `TypeGuard`) on older Python versions and allowing experimentation with features from proposed PEPs before they become standard. This allows developers to write modern,")

**Links:** [Website](https://pypi.org/project/typing-extensions/) | [Documentation](https://typing-extensions.readthedocs.io/) | [GitHub](https://github.com/python/typing_extensions)

---

## <a name='category-testing'></a> Testing Packages

Testing and quality assurance

### coverage (7.8.0)

Code coverage measurement for Python

AgentRunResult(output='Coverage.py is a tool that measures Python code coverage by monitoring program execution to identify which parts of the code have been run and which have not. Key capabilities include branch coverage measurement, measuring subprocesses, and excluding specific code, commonly used to gauge the effectiveness of tests by showing what code they exercise.')

**Links:** [Website](https://pypi.org/project/coverage/) | [Documentation](https://coverage.readthedocs.io/en/7.8.0)

---

### flake8 (7.0.0)

the modular source code checker: pep8 pyflakes and co

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/flake8/)

---

### mypy (1.9.0)

Optional static typing for Python

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/mypy/) | [Documentation](https://mypy.readthedocs.io/en/stable/index.html) | [GitHub](https://github.com/python/mypy)

---

### mypy_extensions (1.1.0)

Type system extensions for programs checked with the mypy type checker.

AgentRunResult(output="The `mypy_extensions` package provides extensions to Python's standard `typing` module, specifically designed for use with the mypy type checker and mypyc compiler. Its key capability is to offer additional type system features not yet in the standard library, enabling developers to write more precise type annotations for improved static analysis and compiled code. This is commonly used by developers seeking to leverage advanced or experimental typing features within the mypy ecosystem.")

**Links:** [Website](https://pypi.org/project/mypy-extensions/)

---

### pylint (3.3.7)

python code static checker

AgentRunResult(output='Pylint is a static code analyzer for Python that examines code without running it to identify errors, enforce coding standards, and detect "code smells." Key capabilities include error checking, style enforcement, and offering refactoring suggestions, making it commonly used by developers to improve code quality and maintainability.')

**Links:** [Website](https://pypi.org/project/pylint/)

---

### pyright (1.1.400)

Command line wrapper for pyright

AgentRunResult(output="The Python package 'pyright' is a command-line wrapper")

**Links:** [Website](https://pypi.org/project/pyright/)

---

### pytest (8.1.1)

pytest: simple powerful testing with Python

AgentRunResult(output='Pytest is a Python package for writing tests, ranging from simple unit tests to complex functional testing for applications and libraries. Key features include its use of plain `assert` statements with detailed failure introspection, auto-discovery of test modules and functions, and scalability. Developers commonly use it to ensure the reliability and correctness of their Python code.')

**Links:** [Website](https://pypi.org/project/pytest/)

---

### pytest-asyncio (0.23.5)

Pytest support for asyncio

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pytest-asyncio/) | [Documentation](https://pytest-asyncio.readthedocs.io)

---

### pytest-cov (4.1.0)

Pytest plugin for measuring coverage.

AgentRunResult(output='Based on the excerpt, `pytest-cov` is a Python package that integrates with pytest to measure code coverage. Key capabilities include support for distributed testing (with `xdist`) and coverage tracking in subprocesses, including those using `multiprocessing`. It is commonly used to generate and manage coverage data files to understand how much code is exercised by tests, especially in parallel or multi')

**Links:** [Website](https://pypi.org/project/pytest-cov/) | [Documentation](https://pytest-cov.readthedocs.io/)

---

### pytest-mock (3.14.0)

Thin-wrapper around the mock package for easier use with pytest

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/pytest-mock/) | [Documentation](https://pytest-mock.readthedocs.io/en/latest/)

---

## <a name='category-data'></a> Data Packages

Data processing, storage, and serialization

### pydantic (2.11.4)

Data validation using Python type hints

**Links:** [Website](https://pypi.org/project/pydantic/) | [Documentation](https://docs.pydantic.dev)

---

### pydantic-evals (0.1.9)

Framework for evaluating stochastic code execution, especially code making use of LLMs

**Links:** [Website](https://pypi.org/project/pydantic-evals/) | [Documentation](https://ai.pydantic.dev/evals)

---

### pydantic-graph (0.1.9)

Graph and state machine library

**Links:** [Website](https://pypi.org/project/pydantic-graph/) | [Documentation](https://ai.pydantic.dev/graph)

---

### pydantic-settings (2.9.1)

Settings management using Pydantic

**Links:** [Website](https://pypi.org/project/pydantic-settings/) | [Documentation](https://docs.pydantic.dev/dev-v2/concepts/pydantic_settings/)

---

### pydantic_core (2.33.2)

Core functionality for Pydantic validation and serialization

AgentRunResult(output='Pydantic-core provides the high-performance (reportedly 17x faster than Pydantic V1) core validation and serialization engine for the Pydantic library, leveraging Rust for speed. It is not intended for direct developer use; rather, it serves as an internal dependency that Pydantic itself utilizes to handle data validation and serialization tasks efficiently.')

**Links:** [Website](https://pypi.org/project/pydantic-core/)

---

### redis (6.0.0)

Python client for Redis database and key-value store

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/redis/) | [Documentation](https://redis.readthedocs.io/en/latest/)

---

### sqlalchemy (2.0.28)

Database Abstraction Library

AgentRunResult(output='')

**Links:** [Website](https://pypi.org/project/SQLAlchemy/) | [Documentation](https://docs.sqlalchemy.org)

---



---

*This document was automatically generated by the Autodoc Agent.*
