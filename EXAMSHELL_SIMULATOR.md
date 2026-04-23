# 42 Exam Rank 02 Simulator

This simulator creates a mock **Exam Rank 02** of 4 questions using exercises from:

- `Level 01`
- `Level 02`

Questions are selected randomly from the local Rank 02 pool (Level 01/02 exercises only).

## Commands

From the repository root:

```sh
./examshell
```

Start a new exam and show question 1.

```sh
./grademe
```

Compile and test your current answer. If it passes, the next question is displayed.

## Where to write your answer

The simulator always tells you the exact file path to edit, for example:

```text
.examshell/work/answer/aff_last_param.c
```

## How grading works

- Your code is compiled with `-Wall -Wextra -Werror`
- The reference solution from this repository is compiled
- Both binaries are run on many generated test cases
- If stdout/stderr/exit code match, the exercise is validated

## Exam state

State and temporary files are stored in:

```text
.examshell/
```

Running `./examshell` starts a fresh Rank 02 exam and resets previous simulator state.

## Optional: run as `examshell` / `grademe` without `./`

If `~/.local/bin` is in your `PATH`:

```sh
mkdir -p ~/.local/bin
ln -sf "$PWD/examshell" ~/.local/bin/examshell
ln -sf "$PWD/grademe" ~/.local/bin/grademe
```

Then you can use:

```sh
examshell
grademe
```
