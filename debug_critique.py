#!/usr/bin/env python3
"""Debug script to test critique formatting"""

import re

# Sample raw critique content that matches what the user is seeing
sample_critique = """
\\1 The statement correctly identifies contradictory results regarding the impact of reduced PICALM expression on amyloid load.
\\2 While the answer suggests PICALM may reduce Aβ production by facilitating APP-CTF transport, the nuances could be clearer.
\\3 The assertion that "PICALM, as part of the endocytic machinery, could be vulnerable to neurodegeneration" is a hypothesis.
"""

print("Original content:")
print(repr(sample_critique))
print("\nOriginal content (display):")
print(sample_critique)

# Current regex from the code
current_regex = r"^\s*(?:\\\\?\d+\s+|\(\d+\)|\d+[\.)]|[-*•])\s*"

print(f"\nCurrent regex: {current_regex}")

raw_lines = [ln.strip() for ln in sample_critique.splitlines() if ln.strip()]
print(f"\nRaw lines: {raw_lines}")

cleaned_lines = []
for ln in raw_lines:
    original = ln
    ln2 = re.sub(current_regex, "", ln)
    print(f"'{original}' -> '{ln2}'")
    cleaned_lines.append(ln2)

print(f"\nCleaned lines: {cleaned_lines}")

# Test improved regex
improved_regex = r"^\s*(?:\\+\d+\s*|\(\d+\)|\d+[\.)]|[-*•])\s*"
print(f"\nImproved regex: {improved_regex}")

improved_cleaned = []
for ln in raw_lines:
    original = ln
    ln2 = re.sub(improved_regex, "", ln)
    print(f"'{original}' -> '{ln2}'")
    improved_cleaned.append(ln2)

print(f"\nImproved cleaned lines: {improved_cleaned}")
