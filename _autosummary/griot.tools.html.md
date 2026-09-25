# griot.tools

The SSOT verbs — plain functions, JSON-able in, JSON-able out.

`python -m griot` dispatches these with `cw`; an MCP or HTTP adapter
references them by string (`griot.tools:write`) and gets a dict back. No
live object crosses the boundary and nothing here prints or exits.

### Functions

| [`quote`](#griot.tools.quote)(topic, \*[, writer, minutes])             | Price the write and the voicing for `topic` before spending anything (research runs; it is free).   |
|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`research`](#griot.tools.research)(topic, \*[, writer])                   | Run the writer's researchers on `topic`; the dossier as JSON.                                       |
| [`write`](#griot.tools.write)(topic, \*[, writer, minutes, angle, ...]) | Research, write, gate; the draft as JSON (and to `out` if given).                                   |
| [`writers`](#griot.tools.writers)()                                       | The writers available, with what a picker needs to show.                                            |

### griot.tools.quote(topic, , writer='general', minutes=0.0)

Price the write and the voicing for `topic` before spending anything (research runs; it is free).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### griot.tools.research(topic, , writer='general')

Run the writer’s researchers on `topic`; the dossier as JSON.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### griot.tools.write(topic, , writer='general', minutes=0.0, angle='', out='', fake=False)

Research, write, gate; the draft as JSON (and to `out` if given).

`fake=True` replaces the LLM with a canned reply so the whole path runs
without a key or a cent — the CLI’s smoke test.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### griot.tools.writers()

The writers available, with what a picker needs to show.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]
