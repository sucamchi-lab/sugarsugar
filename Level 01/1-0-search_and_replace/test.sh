#!/bin/bash

# Compile the program
gcc -Wall -Wextra -Werror search_and_replace.c -o search_and_replace

echo "=== Testing search_and_replace ==="
echo

# Test 1: Basic replacement
echo "Test 1: Basic replacement (replace 'a' with 'o')"
echo "Expected: hollo world"
./search_and_replace "hallo world" "a" "o"
echo

# Test 2: Multiple occurrences
echo "Test 2: Multiple occurrences (replace 'l' with 'z')"
echo "Expected: hezzo worzd"
./search_and_replace "hello world" "l" "z"
echo

# Test 3: Character not found
echo "Test 3: Character not found (replace 'x' with 'y')"
echo "Expected: hello world"
./search_and_replace "hello world" "x" "y"
echo

# Test 4: Single character string
echo "Test 4: Single character (replace 'a' with 'b')"
echo "Expected: b"
./search_and_replace "a" "a" "b"
echo

# Test 5: Empty string (no output expected, just newline)
echo "Test 5: Empty string"
echo "Expected: (blank line)"
./search_and_replace "" "a" "b"
echo

# Test 6: Replace with same character
echo "Test 6: Replace with same character (replace 'a' with 'a')"
echo "Expected: banana"
./search_and_replace "banana" "a" "a"
echo

# Test 7: Too few arguments
echo "Test 7: Too few arguments (only 2 args)"
echo "Expected: (blank line)"
./search_and_replace "hello"
echo

# Test 8: Too many arguments (should only process first 3)
echo "Test 8: Too many arguments"
echo "Expected: (blank line)"
./search_and_replace "hello" "l" "z" "extra"
echo

# Test 9: Replace character with multiple character string (invalid)
echo "Test 9: Invalid - replacement is multiple characters"
echo "Expected: (blank line)"
./search_and_replace "hello" "l" "zz"
echo

# Test 10: Search character is multiple characters (invalid)
echo "Test 10: Invalid - search is multiple characters"
echo "Expected: (blank line)"
./search_and_replace "hello" "ll" "z"
echo

# Cleanup
rm -f search_and_replace
