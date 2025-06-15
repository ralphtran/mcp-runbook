# The Function Factory Approach for decorator mcp.tools from SDK

Of course. You are spot on with your insight! When you see a decorator used with parentheses, like `@mcp.tools()`, it means you are calling a function that *returns* the actual decorator. This is a common pattern for creating configurable decorators and is known as a "decorator factory."

Here is a complete Markdown document explaining the function factory approach to solve your problem.

---
# Dynamically Creating Decorated Functions in Python

This guide explains how to create a function at runtime (e.g., with its name defined in a configuration file) and apply a pre-existing decorator to it. This is a powerful technique for building flexible, data-driven frameworks and plugins.

We will focus on the "Function Factory" approach, which is the safest, most maintainable, and most Pythonic way to achieve this.

## Core Concepts

To understand the solution, two key concepts about Python decorators are essential.

### 1. Decorator Syntax is "Syntactic Sugar"

The `@` symbol is a shortcut. The following two code blocks are equivalent:

```python
# Using the @ syntax
@my_decorator
def my_function():
    print("Hello")

```

```python
# The equivalent code without @
def my_function():
    print("Hello")

my_function = my_decorator(my_function)

```

### 2. Decorators with Arguments (Decorator Factories)

When a decorator is used with parentheses, like `@mcp.tools(mode='strict')`, it is a "decorator factory." It's a function that you call, and it **returns the actual decorator**.

The following two code blocks are equivalent:

```python
# Using the @ syntax with arguments
@mcp.tools(mode='strict')
def my_function():
    print("Hello")

```

```python
# The equivalent code without @
def my_function():
    print("Hello")

# Step 1: Call the factory to get the decorator
the_actual_decorator = mcp.tools(mode='strict')

# Step 2: Apply the returned decorator to the function
my_function = the_actual_decorator(my_function)

```

Understanding this two-step process is the key to creating decorated functions dynamically.

## The Function Factory Approach: Step-by-Step

We will create a function whose name comes from a config and decorate it with `@mcp.tools()`.

### Setup: A Mock SDK

First, let's create a mock `mcp` object to simulate the SDK you are using. This makes our example fully runnable.

```python
# --- Mock SDK: mcp.py ---
# This simulates the SDK you are using.
import functools

class MockTools:
    def __call__(self, mode='default'):
        """
        This is the decorator factory. Calling mcp.tools() executes this.
        It returns the real decorator, `decorator_wrapper`.
        """
        print(f"--- Decorator Factory: Creating a decorator with mode='{mode}' ---")

        def decorator_wrapper(func):
            @functools.wraps(func)
            def inner_wrapper(*args, **kwargs):
                print(f"--- Decorator (mode={mode}): Running pre-execution checks... ---")
                result = func(*args, **kwargs)
                print(f"--- Decorator (mode={mode}): Running post-execution cleanup... ---")
                return result
            return inner_wrapper

        # The factory returns the actual decorator
        return decorator_wrapper

class MockMcp:
    tools = MockTools()

mcp = MockMcp()
# --- End of Mock SDK ---

```

### Step 1: Get the Actual Decorator from the Factory

First, call the decorator factory to get the decorator function we will use. If your decorator takes arguments, provide them here.

```python
# Our config might specify arguments for the decorator
decorator_config = {'mode': 'strict'}

# Call the factory to get the actual decorator function
the_actual_decorator = mcp.tools(**decorator_config)

```

### Step 2: Define the Base Function Logic

Create a regular Python function that contains the core logic you want to execute. This function is "undecorated" for now. Keeping this logic separate makes your code clean and easy to test.

```python
def _base_logic_for_task(filename, content):
    """This is the core logic for our dynamic task."""
    print(f"Executing task: Writing to '{filename}'.")
    # In a real scenario, this would perform a file I/O or API call.
    return f"Wrote {len(content)} characters to {filename}."

```

### Step 3: Manually Apply the Decorator

Now, apply the decorator you obtained in Step 1 to the base function you created in Step 2. This is the crucial step where you manually do what the `@` syntax does automatically.

```python
# Manually apply the decorator to our base function
decorated_function = the_actual_decorator(_base_logic_for_task)

```

### Step 4: Assign the Decorated Function a Dynamic Name

Finally, get the desired function name from your configuration and assign the fully decorated function to a variable with that name. The `globals()` dictionary is a common way to make this new function available throughout the current module.

```python
# Get the dynamic function name from a config file/dict
config = {
    'task_name': 'process_main_file'
}
dynamic_name = config['task_name']

# Assign the decorated function to the global scope with the dynamic name
globals()[dynamic_name] = decorated_function

print(f"Successfully created and decorated function '{dynamic_name}' at runtime.")

```

## Complete Example

Here is the full, runnable code combining all the steps.

```python
import functools

# --- Mock SDK Setup (as defined above) ---
class MockTools:
    def __call__(self, mode='default'):
        print(f"--- Decorator Factory: Creating a decorator with mode='{mode}' ---")
        def decorator_wrapper(func):
            @functools.wraps(func)
            def inner_wrapper(*args, **kwargs):
                print(f"--- Decorator (mode={mode}): Running pre-execution checks... ---")
                result = func(*args, **kwargs)
                print(f"--- Decorator (mode={mode}): Running post-execution cleanup... ---")
                return result
            return inner_wrapper
        return decorator_wrapper

class MockMcp:
    tools = MockTools()

mcp = MockMcp()
# --- End of Mock SDK ---

# === Your Application Code ===

# 1. Get the decorator by calling the factory
decorator_config = {'mode': 'strict'}
the_actual_decorator = mcp.tools(**decorator_config)

# 2. Define the base function logic
def _base_logic_for_task(filename, content):
    """This is the core logic for our dynamic task."""
    print(f"Executing task: Writing to '{filename}'.")
    return f"Wrote {len(content)} characters to {filename}."

# 3. Manually apply the decorator
decorated_function = the_actual_decorator(_base_logic_for_task)

# 4. Assign to a dynamic name from a config
config = {'task_name': 'process_main_file'}
dynamic_name = config['task_name']
globals()[dynamic_name] = decorated_function

print(f"Successfully created and decorated function '{dynamic_name}' at runtime.\\n")

# === Verification ===
# Now you can call the dynamically created function by its new name.
# Note: Linters or IDEs might not recognize it, but it will run correctly.
print(f"--- Calling '{dynamic_name}' ---")
final_result = process_main_file(filename="data.csv", content="id,value\\n1,100")
print(f"--- Call finished ---\\n")

print(f"Result from call: {final_result}")
# Because the decorator used functools.wraps, metadata is preserved from the base function
print(f"Function Name: {process_main_file.__name__}")
print(f"Docstring: {process_main_file.__doc__}")

```

### Execution Output

```
--- Decorator Factory: Creating a decorator with mode='strict' ---
Successfully created and decorated function 'process_main_file' at runtime.

--- Calling 'process_main_file' ---
--- Decorator (mode=strict): Running pre-execution checks... ---
Executing task: Writing to 'data.csv'.
--- Decorator (mode=strict): Running post-execution cleanup... ---
--- Call finished ---

Result from call: Wrote 15 characters to data.csv.
Function Name: _base_logic_for_task
Docstring: This is the core logic for our dynamic task.
```
