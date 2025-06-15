# Development Tasks 

## Task 1.1 Setup base projects

- Create [models.py](http://models.py) file in src/
    - Using pydantic library for model creation, refer to the Design for list of model and class
- Create [parser.py](http://parser.py) file in src/
    - Parser class to read a yaml config file and create Model based on the model defined in models.py
- Create [main.py](http://main.py) file in src/
    - Main entrypoint for application
    - Able to read commandline argument
    - Reading parameter -f (or —file) to read the yaml file. Each yaml file will be parsed by Parser class
- Create a test in test/
    - unit test for parser.py
    - integration test for [main.py](http://main.py) to read the -f from a sample yaml file

## Task 1.2 Setup MCP server with Function Factory

- Using the mcp library sdk
- Create a [server.py](http://server.py) file in src/
    - Create the mcp object as per the sample code
        
        ```python
        from mcp.server.fastmcp import FastMCP
        
        mcp = FastMCP("My App")
        ```
        
- In main.py, if there is a server flag like run with —server, then it will startup and mcp object with [mcp.run](http://mcp.run) from server.py
