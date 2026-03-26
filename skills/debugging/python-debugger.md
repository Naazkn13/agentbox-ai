---
id: debugging-python
name: Python Debugger
category: debugging
level1: "For Python errors, exceptions, and tracebacks"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Python Debugger** — Activate for: Python errors, exceptions, tracebacks, AttributeError, TypeError, KeyError, ValueError, ImportError, assertion failures.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Python Debugger — Core Instructions

1. **Read the full traceback top-to-bottom** before touching any code. The root cause is rarely at the last line shown.
2. **Identify root cause, not symptoms.** Check variable state at the actual error line, not just where it surfaces.
3. **Use targeted logging** — `print(f"DEBUG: {var=}")` right before the failing line. Confirm your assumption before fixing.
4. **Check for None before attribute access.** 90% of AttributeErrors are None objects.
5. **Never suppress exceptions** with bare `except: pass`. Log at minimum: `except Exception as e: logger.error(e)`.
6. **Reproduce the original error first** after fixing — confirm you understood it before moving on.
7. **One change at a time.** Don't batch fixes — you won't know which one worked.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Python Debugger — Full Reference

### Common Error Patterns

**AttributeError: 'NoneType' object has no attribute 'X'**
- Root cause: the object is None where you expect an instance
- Trace back to where the object is created/returned — it's returning None
- Fix: add a None guard (`if obj is None: raise ValueError(...)`) or use `Optional` typing

**KeyError: 'some_key'**
- Root cause: accessing a dict key that doesn't exist
- Fix: use `.get('key', default)` instead of `['key']`; or `key in d` before access

**TypeError: X() takes N positional arguments but M were given**
- Root cause: wrong number of args, or forgot `self` in a method
- Check: is this a method called as a function? Is `self` missing?

**ImportError / ModuleNotFoundError**
- Check: correct package installed in the right virtualenv? (`which python`, `pip list`)
- Check: circular imports — module A imports B which imports A
- Fix circular imports: move shared code to a third `utils.py` module

**RecursionError: maximum recursion depth exceeded**
- Add a base case check at the very top of the recursive function
- Consider an iterative approach using an explicit stack

**ValueError / AssertionError**
- Usually a domain validation failure — read the message carefully
- Add `print(repr(value))` to inspect the exact value causing the failure

### Debugging Tools

```python
# Built-in debugger (Python 3.7+)
breakpoint()   # drops into pdb at this line
# pdb commands: n(ext line), s(tep into), c(ontinue), p <expr>, l(ist), q(uit)

# Inspect object type and attributes
print(type(obj), dir(obj))

# Rich tracebacks (pip install rich)
from rich.traceback import install
install(show_locals=True)   # shows all local variables at each frame

# Structured logging
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
logger.debug(f"Processing {item=!r}, state={state!r}")
```

### Anti-patterns to Avoid
- `except: pass` — silences errors, makes debugging impossible
- `print` debugging without `repr()` — hides None vs "" vs 0 differences
- Fixing the symptom (the line that errors) instead of the cause (why the value is wrong)
- Changing multiple things at once and not knowing what fixed it
<!-- LEVEL 3 END -->
