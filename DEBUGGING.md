# Debugging xv6 with GDB

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
