---
id: clean-code
name: Clean Code & Refactoring
category: refactoring
level1: "For refactoring, clean code principles, DRY, SOLID, and reducing complexity"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Clean Code Expert** — Activate for: refactoring, DRY violations, long functions, complex conditionals, SOLID principles, extract method/class, code smells.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Clean Code — Core Instructions

1. **Functions do one thing.** If you can't describe it without "and", split it.
2. **Names are documentation.** `getUserByEmailAndValidatePassword` is better than `processUser`.
3. **DRY:** if you copy-paste code twice, extract it. But don't over-abstract early — wait for the third instance.
4. **Keep functions short** — aim for < 20 lines. If you need to scroll to read a function, it's too long.
5. **Early returns reduce nesting.** Flip conditions and return early instead of deep if-else chains.
6. **Don't comment what — comment why.** Code explains what; comments explain non-obvious reasoning.
7. **Delete dead code** — version control is your undo button. Don't leave commented-out code.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Clean Code — Full Reference

### Common Refactorings

**Extract Method** (function too long)
```python
# Before
def process_order(order):
    # validate
    if not order.items: raise ValueError("empty")
    if order.total < 0:  raise ValueError("negative total")
    # apply discount
    if order.user.is_premium: order.total *= 0.9
    # charge
    charge_card(order.card, order.total)

# After
def process_order(order):
    _validate_order(order)
    _apply_discount(order)
    charge_card(order.card, order.total)
```

**Early Return** (remove nesting)
```python
# Before
def get_user_email(user_id):
    user = db.find(user_id)
    if user:
        if user.is_active:
            return user.email
    return None

# After
def get_user_email(user_id):
    user = db.find(user_id)
    if not user or not user.is_active:
        return None
    return user.email
```

**Replace Magic Numbers**
```python
# Before
if status == 2: ...       # what is 2?
if retry_count > 3: ...   # why 3?

# After
PUBLISHED = 2
MAX_RETRIES = 3
if status == PUBLISHED: ...
if retry_count > MAX_RETRIES: ...
```

**Replace Conditional with Polymorphism** (SOLID Open/Closed)
```python
# Before: new type = new if branch
def calculate_area(shape):
    if shape.type == 'circle': return pi * shape.radius**2
    if shape.type == 'rect':   return shape.w * shape.h

# After: new type = new class, no existing code changes
class Circle:
    def area(self): return pi * self.radius**2

class Rectangle:
    def area(self): return self.w * self.h
```

### SOLID Quick Reference
- **S** — Single Responsibility: one reason to change
- **O** — Open/Closed: open for extension, closed for modification
- **L** — Liskov Substitution: subclasses must honour parent's contract
- **I** — Interface Segregation: small, specific interfaces over fat ones
- **D** — Dependency Inversion: depend on abstractions, not concretions

### Code Smell Checklist
- [ ] Function > 20 lines → extract
- [ ] More than 3 levels of nesting → early return or extract
- [ ] Same code in 3+ places → extract to shared function
- [ ] Comment explaining what the code does → rename so it's obvious
- [ ] Boolean flag parameter → split into two functions
- [ ] Long parameter list (>4) → use a config object/dataclass
<!-- LEVEL 3 END -->
