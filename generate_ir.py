from llvmlite import ir

# Create a module to hold the function
module = ir.Module(name="example_module")

# Define a function signature: function with no arguments returning an integer
func_type = ir.FunctionType(ir.IntType(32), [])
func = ir.Function(module, func_type, name="example_function")

# Create an entry basic block (the starting point of the function)
entry_block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(entry_block)

# Return a constant value (e.g., 42)
return_value = ir.Constant(ir.IntType(32), 42)
builder.ret(return_value)

# Print the generated IR
print(module)
