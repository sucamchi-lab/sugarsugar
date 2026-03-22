# 42 Exam Shell Practice Repository

Practice repository for 42 C exam exercises, with a local exam shell simulator to train under realistic constraints.

## What this repo contains

- Solved exercises organized by level:
  - Level 00
  - Level 01
  - Level 02
  - Level 03
  - Level 04
  - Level 05
- A local simulator to run mock exams from Levels 00-02:
  - `./examshell` to start an exam
  - `./grademe` to grade the current answer and move to the next question

## Quick start

From the repository root:

```sh
git clone https://github.com/sucamchi-lab/sugarsugar.git
cd sugarsugar
chmod +x examshell grademe
./examshell
```

Then edit the answer file shown by the simulator and run:

```sh
./grademe
```

## Simulator details

See the full simulator guide in [EXAMSHELL_SIMULATOR.md](EXAMSHELL_SIMULATOR.md).

## Recommended practice workflow

1. Start a new mock exam with `./examshell`.
2. Solve each exercise in the generated answer file under `.examshell/work/answer/`.
3. Run `./grademe` after each solution.
4. Repeat regularly to improve speed and reliability.

## Notes

- Grading compiles with `-Wall -Wextra -Werror`.
- The simulator compares your program behavior against the repository reference implementation.
- `.examshell/` is temporary simulator state and is ignored by git.

## Disclaimer

This repository is for learning and practice. Focus on understanding each solution, not memorizing it.
