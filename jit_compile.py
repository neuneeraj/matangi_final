import llvmlite.binding as llvm
from llvmlite import ir

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Create a simple module
module = ir.Module(name="example_module")
func_type = ir.FunctionType(ir.IntType(32), [])
func = ir.Function(module, func_type, name="example_function")
entry_block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(entry_block)
return_value = ir.Constant(ir.IntType(32), 42)
builder.ret(return_value)

# Compile the module
llvm_ir = str(module)
mod = llvm.parse_assembly(llvm_ir)
mod.verify()

# Create a JIT compiler and add the module
target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()
engine = llvm.create_mcjit_compiler(mod, target_machine)

# Compile and run the function
engine.finalize_object()
func_ptr = engine.get_function_address("example_function")

# Convert the function pointer to a callable function
from ctypes import CFUNCTYPE, c_int
cfunc = CFUNCTYPE(c_int)(func_ptr)
result = cfunc()

print("Result from JIT compiled function:", result)
