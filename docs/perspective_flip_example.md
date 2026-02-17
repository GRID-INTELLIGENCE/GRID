# Perspective Flipper - Example Usage

This example demonstrates how the Perspective Flipper transforms documentation into personal action plans.

## Before Transformation (Second-Person)

```markdown
# API Implementation Guide

You should implement authentication using JWT tokens. You need to:

1. Create a secret key in your environment
2. You must ensure the key is at least 32 characters
3. Avoid storing the key in version control
4. Use environment variables instead

When you want to protect a route, you can add the authentication decorator.
If you need to verify permissions, you should check the user's role in the token payload.

Next, you should implement rate limiting to prevent abuse.
```

## After Transformation (First-Person Imperative)

```markdown
# API Implementation Guide

I should implement authentication using JWT tokens. I need to:

1. I must create a secret key in my environment
2. I must ensure the key is at least 32 characters
3. I must avoid storing the key in version control
4. I must use environment variables instead

When I want to protect a route, I can add the authentication decorator.
If I need to verify permissions, I should check the user's role in the token payload.

Next, I must implement rate limiting to prevent abuse.
```

## Usage Commands

**Transform a file:**
```bash
python src/tools/perspective_flip.py docs/guide.md -o docs/my_action_plan.md
```

**Transform implementation plan to personal checklist:**
```bash
python src/tools/perspective_flip.py implementation_plan.md -o MY_PLAN.md
```

**Preview transformation:**
```bash
python src/tools/perspective_flip.py docs/guide.md | head -20
```

## Real-World Use Case

**Before** (from implementation_plan.md):
```
You should create a MessageBroker abstraction. This ensures clean separation.
Next, you can implement retry logic with exponential backoff.
```

**After** (personal action plan):
```
I should create a MessageBroker abstraction. This will ensure clean separation.
Next, I can implement retry logic with exponential backoff.
```

## Why This Matters

- **Accountability**: "You should" → "I should" creates personal ownership
- **Clarity**: Eliminates ambiguity about who performs the action
- **Action-Oriented**: Transforms passive suggestions into active commitments
