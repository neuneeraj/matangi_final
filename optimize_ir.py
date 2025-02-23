import llvmlite.binding as llvm
from llvmlite import ir

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Create a simple module
module = ir.Module(name="complex_module")
func_type = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
func = ir.Function(module, func_type, name="complex_function")
entry_block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(entry_block)

# Create a loop to sum values from 0 to n
n = func.args[0]
i = builder.alloca(ir.IntType(32), name="i")
builder.store(ir.Constant(ir.IntType(32), 0), i)
sum_val = builder.alloca(ir.IntType(32), name="sum")
builder.store(ir.Constant(ir.IntType(32), 0), sum_val)

loop_block = func.append_basic_block(name="loop")
after_loop_block = func.append_basic_block(name="after_loop")

builder.branch(loop_block)
builder.position_at_end(loop_block)

current_i = builder.load(i)
current_sum = builder.load(sum_val)
next_i = builder.add(current_i, ir.Constant(ir.IntType(32), 1))
next_sum = builder.add(current_sum, current_i)
builder.store(next_i, i)
builder.store(next_sum, sum_val)

builder.cbranch(builder.icmp_signed('<', next_i, n), loop_block, after_loop_block)

builder.position_at_end(after_loop_block)
result = builder.load(sum_val)
builder.ret(result)

# Compile the module
llvm_ir = str(module)
mod = llvm.parse_assembly(llvm_ir)
mod.verify()

# Create PassManager for optimizations
pass_manager = llvm.create_module_pass_manager()
pass_manager.add_constant_merge_pass()
pass_manager.add_dead_arg_elimination_pass()
pass_manager.add_instruction_combining_pass()
pass_manager.add_cfg_simplification_pass()
pass_manager.add_loop_unroll_pass()  # Unroll loops for performance
pass_manager.add_gvn_pass()  # Global Value Numbering
pass_manager.add_tail_call_elimination_pass()  # Tail Call Elimination

# Set a reasonable threshold for function inlining
threshold = 100
pass_manager.add_function_inlining_pass(threshold)

# Run the pass manager on the module
pass_manager.run(mod)

# Print the optimized IR
print(mod)
