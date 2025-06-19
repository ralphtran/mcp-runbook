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

- Using the mcp library sdk in our project

```bash
uv add mcp
```

- Create a [server.py](http://server.py) file in src/
    - Create the mcp object as per the sample code

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")
```

- In the server.py, there will be a logic to build the mcp server based on the config in yaml
    - For each tool defined in the yaml config, create a function in python. The function should have the name same as tool name defined in yaml.
        - Function name should be converted to valid python function name
    - For each tool config in yaml, create a Tool object in mcp sdk
        - Using mcp.tools() function
        - Passing name from the yaml name
        - Passing description from the yaml name
    - In the function, there will be subprocess to run all the steps as command. It will loop all the step and:
        - Subprocess should get the environment variable from the current environment variable. Then it will add the variable defined in the `env` block in `step`.
        - If `cwd` is defined in the step, then subprocess will change working directory to that directory before execute the command in the step
        - Print the output that Step [<step number>/<total steps>] <step name> is running. Example: Step [1/5] Hello World is running
        - To avoid blocking call, program should use asyncio subprocess
- In main.py, if there is a server flag like run with —server, then it will startup and mcp object with [mcp.run](http://mcp.run)() from server.py
