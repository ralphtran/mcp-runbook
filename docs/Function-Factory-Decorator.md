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

# Function Factory wrapper with arguments and `inspect` module
Excellent question! This is a more advanced and very practical use case for function factories. You're moving from a generic `**kwargs` interface to a specific, self-documenting, and type-hinted function signature.

The standard and **strongly suggested way** to achieve this is by using Python's built-in `inspect` module. You can dynamically build a function signature and attach it to a wrapper function.

This approach is far superior to using `exec()` because it's safer, cleaner, and works well with linters, type checkers (like Mypy), and IDEs.

### The Goal

-   **Start with:** A generic async function that takes a dictionary: `async def tool_logic_inner(**parameters: Dict[str, str])`
-   **End with:** A specific async function that *looks and feels* like a normal function: `async def hello_name(name: str) -> str`

### The Strategy: Using `inspect.Signature`

1.  **Define the Core Logic:** Keep your generic function that operates on the `parameters` dictionary. This separates the *implementation* from the *interface*.
2.  **Create a Factory Function:** This factory will take the desired function name, its parameters (name and type), and a docstring.
3.  **Build the Signature:** Inside the factory, use `inspect.Parameter` to define each argument and `inspect.Signature` to combine them.
4.  **Create a Wrapper:** Define a simple `async def wrapper(*args, **kwargs)` function. This wrapper's job is to translate the user-friendly arguments into the dictionary format your core logic expects.
5.  **Apply the Signature:** Assign the dynamically created signature to the wrapper's `__signature__` attribute. Also set its `__name__` and `__doc__`.
6.  **Return the Wrapper:** The factory returns this new, beautified wrapper function.

---

### Complete Code Example

Let's build a factory called `create_tool_function` that does exactly this.

```python
import inspect
from typing import Dict, Any, Callable, Coroutine

# 1. THE CORE LOGIC
# This is your generic implementation. It's kept separate and only deals with a dictionary.
async def _core_tool_logic(**parameters: str) -> str:
    """The actual implementation logic for various tools."""
    
    # Example logic for a "hello_name" tool
    if "name" in parameters:
        name = parameters["name"]
        return f"Hello, {name}! It's a pleasure to meet you."
    
    # Example logic for another tool
    if "item" in parameters and "quantity" in parameters:
        item = parameters['item']
        quantity = parameters['quantity']
        return f"Confirmed: Order placed for {quantity} of {item}."
        
    return "Error: Could not execute the tool with the given parameters."


# 2. THE FUNCTION FACTORY
def create_tool_function(
    name: str,
    params: Dict[str, Any],
    docstring: str = "",
) -> Callable[..., Coroutine[Any, Any, str]]:
    """
    Factory to create a specific, nicely-signatured async tool function.

    Args:
        name (str): The desired name for the new function.
        params (Dict[str, Any]): A dictionary mapping parameter names to their types.
                                 Example: {'name': str, 'age': int}
        docstring (str): The docstring for the new function.

    Returns:
        A new async function with a specific signature that calls the core logic.
    """
    # 3. Build the list of inspect.Parameter objects from the params dict
    signature_params = [
        inspect.Parameter(
            name=param_name,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, # Standard parameter type
            annotation=param_type
        ) for param_name, param_type in params.items()
    ]
    
    # Create the full signature object
    new_signature = inspect.Signature(signature_params)

    # 4. Create the wrapper function that will be returned
    async def wrapper(*args, **kwargs) -> str:
        """A dynamically generated wrapper."""
        # This binds the incoming args/kwargs to the signature we created.
        # It normalizes the arguments into a single dictionary, which is perfect
        # for our core logic function. It also validates the arguments!
        bound_args = new_signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Call the generic core logic with the prepared dictionary of arguments
        return await _core_tool_logic(**bound_args.arguments)

    # 5. Apply the new signature and metadata to the wrapper
    wrapper.__name__ = name
    wrapper.__doc__ = docstring
    wrapper.__signature__ = new_signature
    
    # 6. Return the finished, user-friendly function
    return wrapper

# --- How to use the factory ---

# Create the 'hello_name' function
hello_name = create_tool_function(
    name="hello_name",
    params={"name": str},
    docstring="Greets the user by their name."
)

# Create another, more complex tool function from the same core logic
order_item = create_tool_function(
    name="order_item",
    params={"item": str, "quantity": int}, # Note: core logic treats it as str, but signature shows int
    docstring="Places an order for a given quantity of an item."
)

# --- Now, let's test our new functions ---

import asyncio

async def main():
    # Test the first function
    # You can call it like a normal function with keyword arguments
    result1 = await hello_name(name="Alice")
    print(result1) # Output: Hello, Alice! It's a pleasure to meet you.
    
    # Test the second function
    result2 = await order_item(item="Laptop", quantity=2)
    print(result2) # Output: Confirmed: Order placed for 2 of Laptop.

    # --- Let's inspect the functions to prove it worked ---
    print("-" * 20)
    
    # Check the signature of hello_name
    print(f"Function: {hello_name.__name__}")
    print(f"Signature: {inspect.signature(hello_name)}")
    print(f"Docstring: {hello_name.__doc__}")

    print("-" * 20)
    
    # Check the signature of order_item
    print(f"Function: {order_item.__name__}")
    print(f"Signature: {inspect.signature(order_item)}")
    print(f"Docstring: {order_item.__doc__}")

    # It even raises a proper TypeError if you call it incorrectly!
    try:
        await hello_name(wrong_param="Bob")
    except TypeError as e:
        print(f"\nCaught expected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Why This Is The Suggested Way

1.  **IDE and Tooling Friendly:** Your IDE (like VS Code or PyCharm), static analyzers (Mypy), and linters will recognize the new signature. You get autocompletion, type checking, and parameter validation for free.
2.  **Self-Documenting API:** Calling `help(hello_name)` or `inspect.signature(hello_name)` shows the *real*, user-facing signature, not a generic `**kwargs`. This makes your code much easier to use and understand.
3.  **Safety and Robustness:** `new_signature.bind()` automatically validates that the function was called with the correct arguments, raising a `TypeError` if not. This is much safer than manually digging through a `kwargs` dictionary.
4.  **Separation of Concerns:** The `_core_tool_logic` contains the business logic, while `create_tool_function` handles the presentation and interface. This makes your code cleaner and easier to maintain.
5.  **No `exec()`:** It avoids the security risks, debugging nightmares, and performance overhead of building and executing code strings with `exec()`.
