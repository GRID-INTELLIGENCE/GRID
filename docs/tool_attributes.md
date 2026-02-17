# Tool Attribute System

The tool attribute system provides a standardized way to define and verify the properties of various tools in the system.

## Core Attributes

Each tool is defined by five key attributes:

1. **Access** - Defines the type of access:
   - `read_only`: Only reads data
   - `write`: Only writes data
   - `read_write`: Both reads and writes
   - `simulate_only`: Performs analysis without side effects

2. **Scope** - Defines the target scope:
   - `single_target`: Operates on one file/resource
   - `multi_target`: Operates on multiple files/resources
   - `partial`: Works on a slice/sample of data
   - `full`: Works on entire artifacts

3. **Depth** - Defines the processing depth:
   - `literal`: Works with verbatim bytes/text
   - `structural`: Works with AST/sections/headers
   - `semantic`: Understands meaning/intent
   - `temporal`: Handles changes over time

4. **Transform** - Defines the transformation applied:
   - `none`: Pure read/write
   - `summarize`: Creates summaries
   - `compress`: Reduces size
   - `translate`: Changes representation
   - `normalize`: Standardizes data
   - `cross_reference`: Links artifacts

5. **Interaction** - Defines the execution mode:
   - `synchronous`: Blocking execution
   - `streaming`: Incremental processing
   - `batch`: Processes sets of data

## Standard Tool Properties

Common tool patterns are predefined:
