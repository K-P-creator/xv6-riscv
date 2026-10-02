# Debugging xv6 with GDB

## Select a user program for QEMU tracing

The tracing plugin uses the selected user executable to generate user-PC
symbol labels. From the repository root, pass its built path to `make qemu`
with `USER_PROGRAM`:

```sh
make qemu USER_PROGRAM=user/_bubblesort
```

For another program included in `UPROGS`, use its corresponding executable,
for example:

```sh
make qemu USER_PROGRAM=user/_cat
```

`USER_PROGRAM` selects the executable used to generate the plugin's user-PC
labels; it does not select which command xv6 runs after boot. At the xv6 shell,
run the desired program separately. If the variable is omitted, the default
for symbol generation is `user/_bubblesort`.

## Analyze a QEMU trace

The scripts in [`tools/`](./tools/) inspect the CSV written by the tracing
plugin. Run them from the repository root with Python 3:

```sh
python3 tools/trace_summary.py qemu-trace.csv --symbols user/bubblesort.sym
python3 tools/trace_address.py qemu-trace.csv 0x5f78 --symbols user/bubblesort.sym --follow-pointer
python3 tools/trace_symbols.py qemu-trace.csv user/bubblesort.sym
python3 tools/trace_memory.py qemu-trace.csv --array-base 0x14fe0 --count 5
python3 tools/trace_disasm.py qemu-trace.csv user/_bubblesort --symbols user/bubblesort.sym
```

`trace_address.py` filters accesses by guest virtual address and can optionally
show accesses to values read from that address. `trace_memory.py` replays
observed writes to an address or snapshots aligned 4-byte array writes.
`trace_disasm.py` joins memory accesses to the instruction at each PC and
requires a RISC-V `objdump`. The symbol file must match the executable that
generated the trace. Since trace rows may omit accesses and do not identify
the process, reconstructed memory state and inferred variable identities are
evidence, not guaranteed complete source-level facts.

## Start a debugging session

In terminal 1, from the xv6 repository root, run:

```sh
make qemu-gdb
```

Leave this terminal running. In terminal 2, start GDB with the kernel symbols:

```sh
gdb-multiarch kernel/kernel
```

`gdb-multiarch` is required because xv6 runs RISC-V code. Install it with:

```sh
sudo apt install gdb-multiarch
```

The generated `.gdbinit` file connects GDB to QEMU automatically. If GDB
does not load it because of its auto-load security setting, run these
commands at the GDB prompt:

```
gdb -ex "set architecture riscv:rv64" -ex "target remote localhost:PORT" -ex "file kernel/kernel" -ex "tui enable"
```

```gdb
set architecture riscv:rv64
target remote localhost:PORT
file kernel/kernel
```

Replace `PORT` with the number printed by `make print-gdbport`.

Useful commands include:

```gdb
tui enable
break main
continue
break consoleintr
next
print <variable>
print *<address>
backtrace
info registers
list
```

## Make a custom GDB command

Add a `define` block to
[`.gdbinit.tmpl-riscv`](./.gdbinit.tmpl-riscv). For example, this command
sets a breakpoint on the console interrupt handler and continues execution:

```gdb
define break-console
  break consoleintr
  continue
end
```

After restarting `make qemu-gdb` and GDB, use it like this:

```gdb
break-console
```

For a command that prints the character received by the console, use:

```gdb
define watch-console
  break consoleintr
  commands
    silent
    printf "console input: %d\n", c
    continue
  end
end
```

When debugging a user program, use its symbol file for source-level
breakpoints after xv6 has loaded it:

```gdb
add-symbol-file user/_bubblesort
break main
```

Pressing Ctrl-C in the GDB terminal interrupts GDB itself. To send Ctrl-C to
the xv6 console, type it in the terminal running QEMU. If the kernel's
console handler receives it, it terminates the active user process; when xv6
is idle, the configured QEMU test device powers QEMU off.
