import llvmlite.binding as llvm
from llvmlite import ir
import ctypes  # Add this import

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Create a simple module
module = ir.Module(name="linear_regression_module")
func_type = ir.FunctionType(ir.VoidType(), [ir.IntType(32).as_pointer(), ir.IntType(32).as_pointer(), ir.IntType(32)])
func = ir.Function(module, func_type, name="linear_regression")
entry_block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(entry_block)

# Function arguments
x_ptr = func.args[0]
y_ptr = func.args[1]
n = func.args[2]

# Sum(x), Sum(y), Sum(x*x), Sum(x*y)
sum_x = builder.alloca(ir.IntType(32), name="sum_x")
sum_y = builder.alloca(ir.IntType(32), name="sum_y")
sum_xx = builder.alloca(ir.IntType(32), name="sum_xx")
sum_xy = builder.alloca(ir.IntType(32), name="sum_xy")

builder.store(ir.Constant(ir.IntType(32), 0), sum_x)
builder.store(ir.Constant(ir.IntType(32), 0), sum_y)
builder.store(ir.Constant(ir.IntType(32), 0), sum_xx)
builder.store(ir.Constant(ir.IntType(32), 0), sum_xy)

i = builder.alloca(ir.IntType(32), name="i")
builder.store(ir.Constant(ir.IntType(32), 0), i)

loop_block = func.append_basic_block(name="loop")
after_loop_block = func.append_basic_block(name="after_loop")

builder.branch(loop_block)
builder.position_at_end(loop_block)

current_i = builder.load(i)
current_x_ptr = builder.gep(x_ptr, [current_i])
current_y_ptr = builder.gep(y_ptr, [current_i])
current_x = builder.load(current_x_ptr)
current_y = builder.load(current_y_ptr)

sum_x_val = builder.load(sum_x)
sum_y_val = builder.load(sum_y)
sum_xx_val = builder.load(sum_xx)
sum_xy_val = builder.load(sum_xy)

next_sum_x = builder.add(sum_x_val, current_x)
next_sum_y = builder.add(sum_y_val, current_y)
next_sum_xx = builder.add(sum_xx_val, builder.mul(current_x, current_x))
next_sum_xy = builder.add(sum_xy_val, builder.mul(current_x, current_y))

builder.store(next_sum_x, sum_x)
builder.store(next_sum_y, sum_y)
builder.store(next_sum_xx, sum_xx)
builder.store(next_sum_xy, sum_xy)

next_i = builder.add(current_i, ir.Constant(ir.IntType(32), 1))
builder.store(next_i, i)

builder.cbranch(builder.icmp_signed('<', next_i, n), loop_block, after_loop_block)

builder.position_at_end(after_loop_block)

# Calculate coefficients m (slope) and b (intercept)
# m = (n*sum_xy - sum_x*sum_y) / (n*sum_xx - sum_x*sum_x)
# b = (sum_y - m*sum_x) / n

sum_x_val = builder.load(sum_x)
sum_y_val = builder.load(sum_y)
sum_xx_val = builder.load(sum_xx)
sum_xy_val = builder.load(sum_xy)

n_val = builder.sitofp(n, ir.FloatType())
sum_x_float = builder.sitofp(sum_x_val, ir.FloatType())
sum_y_float = builder.sitofp(sum_y_val, ir.FloatType())
sum_xx_float = builder.sitofp(sum_xx_val, ir.FloatType())
sum_xy_float = builder.sitofp(sum_xy_val, ir.FloatType())

numerator_m = builder.fsub(builder.fmul(n_val, sum_xy_float), builder.fmul(sum_x_float, sum_y_float))
denominator_m = builder.fsub(builder.fmul(n_val, sum_xx_float), builder.fmul(sum_x_float, sum_x_float))
m = builder.fdiv(numerator_m, denominator_m)

numerator_b = builder.fsub(sum_y_float, builder.fmul(m, sum_x_float))
b = builder.fdiv(numerator_b, n_val)

# Define the coefficients as global variables
m_global = ir.GlobalVariable(module, ir.FloatType(), name="m_value")
m_global.initializer = ir.Constant(ir.FloatType(), 0.0)
m_global.linkage = 'common'
b_global = ir.GlobalVariable(module, ir.FloatType(), name="b_value")
b_global.initializer = ir.Constant(ir.FloatType(), 0.0)
b_global.linkage = 'common'

# Store computed values into globals
builder.store(m, m_global)
builder.store(b, b_global)

builder.ret_void()

# Compile the module
llvm_ir = str(module)
mod = llvm.parse_assembly(llvm_ir)
mod.verify()

# Print the generated IR
print(mod)

# Create and run the JIT compiler
llvm.initialize_all_targets()
llvm.initialize_all_asmprinters()
target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()
engine = llvm.create_mcjit_compiler(mod, target_machine)

engine.finalize_object()
engine.run_static_constructors()

# Example data: x_values and y_values
x_values = [1, 2, 3, 4, 5]
y_values = [2, 4, 6, 8, 10]
n = len(x_values)

# Allocate arrays for input data
x_array = (ctypes.c_int * n)(*x_values)
y_array = (ctypes.c_int * n)(*y_values)

# Call the compiled function
linear_regression_func_ptr = engine.get_function_address("linear_regression")
linear_regression_func = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int)(linear_regression_func_ptr)
linear_regression_func(x_array, y_array, n)

# Retrieve the global variables
m_addr = engine.get_global_value_address("m_value")
b_addr = engine.get_global_value_address("b_value")

# Convert the pointers to floats
m_value = ctypes.cast(m_addr, ctypes.POINTER(ctypes.c_float)).contents.value
b_value = ctypes.cast(b_addr, ctypes.POINTER(ctypes.c_float)).contents.value

print(f"Slope (m): {m_value}, Intercept (b): {b_value}")
