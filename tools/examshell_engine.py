#!/usr/bin/env python3

import argparse
from collections import Counter
import json
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".examshell"
STATE_FILE = STATE_DIR / "state.json"
WORK_DIR = STATE_DIR / "work"
ANSWER_DIR = WORK_DIR / "answer"
BUILD_DIR = WORK_DIR / "build"

LEVEL_DIRS = ["Level 00", "Level 01", "Level 02"]
QUESTION_LEVEL_SEQUENCE = [0, 0, 1, 1, 1, 1, 1, 2, 2, 2]
QUESTIONS_PER_LEVEL = dict(Counter(QUESTION_LEVEL_SEQUENCE))
TOTAL_QUESTIONS = 10
TIMEOUT_SECONDS = 1.5
TEST_CASES = 50


@dataclass
class Question:
    level: int
    bucket: int
    exercise: str
    exercise_dir: Path
    source_file: Path
    subject_file: Path
    has_main: bool

    def to_dict(self) -> Dict[str, str]:
        return {
            "level": self.level,
            "bucket": self.bucket,
            "exercise": self.exercise,
            "exercise_dir": str(self.exercise_dir),
            "source_file": str(self.source_file),
            "subject_file": str(self.subject_file),
            "has_main": self.has_main,
        }


def parse_level_and_bucket(dirname: str) -> Tuple[int, int]:
    match = re.match(r"^(\d+)-(\d+)-", dirname)
    if not match:
        raise ValueError(f"Invalid exercise directory name: {dirname}")
    return int(match.group(1)), int(match.group(2))


def has_main_function(source: Path) -> bool:
    try:
        content = source.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return re.search(r"\bmain\s*\(", content) is not None


def discover_questions() -> List[Question]:
    questions: List[Question] = []
    for level_dir in LEVEL_DIRS:
        base = REPO_ROOT / level_dir
        if not base.exists():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            try:
                level, bucket = parse_level_and_bucket(entry.name)
            except ValueError:
                continue

            source_candidates = sorted(
                p
                for p in entry.glob("*.c")
                if p.name != "test.c" and p.name != "main.c"
            )
            subject_file = entry / "subject.en.txt"
            if not source_candidates or not subject_file.exists():
                continue

            source_file = source_candidates[0]
            source_has_main = has_main_function(source_file)

            questions.append(
                Question(
                    level=level,
                    bucket=bucket,
                    exercise=entry.name,
                    exercise_dir=entry,
                    source_file=source_file,
                    subject_file=subject_file,
                    has_main=source_has_main,
                )
            )

    questions.sort(key=lambda q: (q.level, q.bucket, q.exercise))
    return questions


def choose_exam_questions(all_questions: List[Question]) -> List[Question]:
    grouped: Dict[int, List[Question]] = {0: [], 1: [], 2: []}
    for q in all_questions:
        if q.level in grouped:
            grouped[q.level].append(q)

    rng = random.Random()
    for level, pool in grouped.items():
        rng.shuffle(pool)

    selected: List[Question] = []
    for level in QUESTION_LEVEL_SEQUENCE:
        selected.append(grouped[level].pop())

    return selected


def reset_workdirs() -> None:
    if STATE_DIR.exists() and not STATE_DIR.is_dir():
        raise RuntimeError(f"Path exists and is not a directory: {STATE_DIR}")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    ANSWER_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def write_state(state: Dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def read_state() -> Dict:
    if not STATE_FILE.exists():
        raise RuntimeError("No active exam. Run 'examshell' first.")
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def seed_answer_file(question: Dict) -> Path:
    source_name = Path(question["source_file"]).name
    target = ANSWER_DIR / source_name
    stub = textwrap.dedent(
        f"""\
        /*
        ** 42 examshell simulator
        ** Exercise: {question['exercise']}
        ** Fill this file, then run: grademe
        */

        """
    )
    target.write_text(stub, encoding="utf-8")
    return target


def display_question(state: Dict) -> None:
    idx = state["current_index"]
    question = state["questions"][idx]
    source_name = Path(question["source_file"]).name
    answer_path = ANSWER_DIR / source_name
    subject = Path(question["subject_file"]).read_text(
        encoding="utf-8", errors="ignore")

    print(f"Question {idx + 1}/{len(state['questions'])}")
    print(f"Level {question['level']:02d} | {question['exercise']}")
    print(f"Edit your answer in: {answer_path}")
    print("-" * 72)
    print(subject.strip())
    print("-" * 72)
    print("When ready, run: grademe")


def compile_c(source: Path, output: Path) -> Tuple[bool, str]:
    return compile_c_sources([source], output)


def compile_c_sources(sources: List[Path], output: Path) -> Tuple[bool, str]:
    cmd = [
        "gcc",
        "-Wall",
        "-Wextra",
        "-Werror",
        *(str(src) for src in sources),
        "-o",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, (result.stdout + result.stderr).strip()
    return True, ""


def random_word(rng: random.Random, min_len: int = 0, max_len: int = 16) -> str:
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-+*/!@#$%^&()[]{}"
    size = rng.randint(min_len, max_len)
    return "".join(rng.choice(chars) for _ in range(size))


def build_test_cases(seed: int) -> List[Tuple[List[str], str]]:
    rng = random.Random(seed)
    cases: List[Tuple[List[str], str]] = []
    base_argv = [
        [],
        ["a"],
        ["abc"],
        ["42"],
        ["-42"],
        ["hello", "world"],
        ["abc", "a", "b"],
        ["   spaced"],
        ["", ""],
        ["foo", "bar", "baz"],
    ]
    base_stdin = ["", "\n", "abc\n", "42\n",
                  "   -15\n", "Hello World\n", "a b c\n"]

    for argv in base_argv:
        for stdin_text in base_stdin[:3]:
            cases.append((argv[:], stdin_text))

    while len(cases) < TEST_CASES:
        argc = rng.randint(0, 5)
        argv = [random_word(rng) for _ in range(argc)]
        stdin_text = "\n".join(random_word(rng, 0, 20)
                               for _ in range(rng.randint(0, 3)))
        if stdin_text:
            stdin_text += "\n"
        cases.append((argv, stdin_text))

    return cases[:TEST_CASES]


def run_binary(path: Path, argv: List[str], stdin_text: str) -> Tuple[int, bytes, bytes, bool]:
    try:
        result = subprocess.run(
            [str(path), *argv],
            input=stdin_text.encode("utf-8"),
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
        return result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout if exc.stdout is not None else b""
        err = exc.stderr if exc.stderr is not None else b""
        return 124, out, err, True


def compare_outputs(ref_bin: Path, user_bin: Path, seed: int) -> Tuple[bool, str]:
    cases = build_test_cases(seed)
    for i, (argv, stdin_text) in enumerate(cases, start=1):
        ref_rc, ref_out, ref_err, ref_to = run_binary(
            ref_bin, argv, stdin_text)
        usr_rc, usr_out, usr_err, usr_to = run_binary(
            user_bin, argv, stdin_text)
        if (ref_rc, ref_out, ref_err, ref_to) != (usr_rc, usr_out, usr_err, usr_to):
            debug = []
            debug.append(f"Mismatch on test #{i}")
            debug.append(f"argv: {argv}")
            if stdin_text:
                debug.append(f"stdin: {stdin_text!r}")
            else:
                debug.append("stdin: <empty>")
            debug.append(f"expected rc={ref_rc}, timeout={ref_to}")
            debug.append(f"got      rc={usr_rc}, timeout={usr_to}")
            debug.append(
                f"expected stdout={ref_out.decode('utf-8', errors='replace')!r}")
            debug.append(
                f"got      stdout={usr_out.decode('utf-8', errors='replace')!r}")
            debug.append(
                f"expected stderr={ref_err.decode('utf-8', errors='replace')!r}")
            debug.append(
                f"got      stderr={usr_err.decode('utf-8', errors='replace')!r}")
            return False, "\n".join(debug)
    return True, ""


def build_function_harness(exercise: str) -> str:
    harnesses = {
        "0-0-ft_print_numbers": r'''#include <unistd.h>

void ft_print_numbers(void);

int main(void)
{
    ft_print_numbers();
    return 0;
}
''',
        "1-0-ft_strcpy": r'''#include <stdio.h>

char *ft_strcpy(char *s1, char *s2);

int main(void)
{
    char buf[128];
    char *cases[] = {"", "a", "abc", "with spaces", "42", "hello42school", "!@#$"};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        char *ret = ft_strcpy(buf, cases[i]);
        printf("%s|%d\n", buf, ret == buf);
        i++;
    }
    return 0;
}
''',
        "1-0-ft_strlen": r'''#include <stdio.h>

int ft_strlen(char *str);

int main(void)
{
    char *cases[] = {"", "a", "abc", "with spaces", "1234567890", "Hello, World!"};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        printf("%d\n", ft_strlen(cases[i]));
        i++;
    }
    return 0;
}
''',
        "1-2-ft_putstr": r'''#include <unistd.h>

void ft_putstr(char *str);

int main(void)
{
    char *cases[] = {"", "a", "abc", "with spaces", "Hello, World!"};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        ft_putstr(cases[i]);
        write(1, "\n", 1);
        i++;
    }
    return 0;
}
''',
        "1-2-ft_swap": r'''#include <stdio.h>
#include <limits.h>

void ft_swap(int *a, int *b);

int main(void)
{
    int a;
    int b;
    int cases[][2] = {
        {0, 0},
        {1, 2},
        {-5, 7},
        {INT_MIN, INT_MAX},
        {42, -42}
    };
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        a = cases[i][0];
        b = cases[i][1];
        ft_swap(&a, &b);
        printf("%d,%d\n", a, b);
        i++;
    }
    return 0;
}
''',
        "1-5-ft_atoi": r'''#include <stdio.h>

int ft_atoi(const char *str);

int main(void)
{
    char *cases[] = {
        "0",
        "42",
        "-42",
        "+17",
        "   2147483647",
        "\t\n\r\v\f 123",
        "--1",
        "+-2",
        "42abc",
        "abc42",
        ""
    };
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        printf("%d\n", ft_atoi(cases[i]));
        i++;
    }
    return 0;
}
''',
        "1-6-ft_putnbr": r'''#include <unistd.h>
#include <limits.h>

void ft_putnbr(int nb);

int main(void)
{
    int cases[] = {0, 1, -1, 42, -42, INT_MAX, INT_MIN};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        ft_putnbr(cases[i]);
        write(1, "\n", 1);
        i++;
    }
    return 0;
}
''',
        "2-0-ft_strdup": r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *ft_strdup(char *src);

int main(void)
{
    char source[128];
    char expected[128];
    char *dup;
    char *cases[] = {"", "a", "abc", "with spaces", "Hello, World!", "1234567890"};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        strcpy(source, cases[i]);
        strcpy(expected, source);
        dup = ft_strdup(source);
        if (!dup)
        {
            printf("NULL\n");
            i++;
            continue;
        }
        if (source[0])
            source[0] = '#';
        printf("%s|%d\n", dup, strcmp(dup, expected) == 0);
        free(dup);
        i++;
    }
    return 0;
}
''',
        "2-1-max": r'''#include <stdio.h>

int max(int *tab, unsigned int len);

int main(void)
{
    int a[] = {1, 2, 3, 4, 5};
    int b[] = {-10, -3, -50, -1};
    int c[] = {42};
    int d[] = {0, 100, -100, 99, 100};

    printf("%d\n", max(a, 5));
    printf("%d\n", max(b, 4));
    printf("%d\n", max(c, 1));
    printf("%d\n", max(d, 5));
    printf("%d\n", max(d, 0));
    return 0;
}
''',
        "2-5-ft_strcmp": r'''#include <stdio.h>

int ft_strcmp(char *s1, char *s2);

int main(void)
{
    char *a[] = {"", "a", "abc", "abc", "abcd", "abc", "with spaces"};
    char *b[] = {"", "b", "abc", "ab", "abc", "abcd", "with  spaces"};
    int i;

    i = 0;
    while (i < (int)(sizeof(a) / sizeof(a[0])))
    {
        printf("%d\n", ft_strcmp(a[i], b[i]));
        i++;
    }
    return 0;
}
''',
        "2-5-ft_strrev": r'''#include <stdio.h>

char *ft_strrev(char *str);

int main(void)
{
    char s0[32] = "";
    char s1[32] = "a";
    char s2[32] = "ab";
    char s3[32] = "abcde";
    char s4[32] = "with spaces";
    char *cases[] = {s0, s1, s2, s3, s4};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        char *ret = ft_strrev(cases[i]);
        printf("%s|%d\n", cases[i], ret == cases[i]);
        i++;
    }
    return 0;
}
''',
        "2-6-is_power_of_2": r'''#include <stdio.h>

int is_power_of_2(unsigned int n);

int main(void)
{
    unsigned int cases[] = {0, 1, 2, 3, 4, 5, 8, 16, 31, 32, 1024, 1025};
    int i;

    i = 0;
    while (i < (int)(sizeof(cases) / sizeof(cases[0])))
    {
        printf("%d\n", is_power_of_2(cases[i]));
        i++;
    }
    return 0;
}
''',
    }
    return harnesses.get(exercise, "")


def compare_function_exercise_outputs(ref_source: Path, user_source: Path, exercise: str) -> Tuple[bool, str]:
    harness_src = build_function_harness(exercise)
    if not harness_src:
        return False, f"Internal error: no test harness defined for function exercise '{exercise}'."

    driver = BUILD_DIR / "driver.c"
    ref_bin = BUILD_DIR / "ref.out"
    usr_bin = BUILD_DIR / "user.out"
    driver.write_text(harness_src, encoding="utf-8")

    ok, log = compile_c_sources([ref_source, driver], ref_bin)
    if not ok:
        return False, (
            "Internal error: failed to compile reference solution with generated harness.\n"
            + log
        )

    ok, log = compile_c_sources([user_source, driver], usr_bin)
    if not ok:
        return False, "KO: your code does not compile with -Wall -Wextra -Werror\n" + log

    ref_rc, ref_out, ref_err, ref_to = run_binary(ref_bin, [], "")
    usr_rc, usr_out, usr_err, usr_to = run_binary(usr_bin, [], "")

    if (ref_rc, ref_out, ref_err, ref_to) != (usr_rc, usr_out, usr_err, usr_to):
        debug = []
        debug.append("Mismatch on generated harness tests")
        debug.append(f"expected rc={ref_rc}, timeout={ref_to}")
        debug.append(f"got      rc={usr_rc}, timeout={usr_to}")
        debug.append(
            f"expected stdout={ref_out.decode('utf-8', errors='replace')!r}")
        debug.append(
            f"got      stdout={usr_out.decode('utf-8', errors='replace')!r}")
        debug.append(
            f"expected stderr={ref_err.decode('utf-8', errors='replace')!r}")
        debug.append(
            f"got      stderr={usr_err.decode('utf-8', errors='replace')!r}")
        return False, "\n".join(debug)

    return True, ""


def command_start(_: argparse.Namespace) -> int:
    all_questions = discover_questions()
    available_per_level = Counter(q.level for q in all_questions)
    missing_levels = [
        level for level, needed in QUESTIONS_PER_LEVEL.items()
        if available_per_level.get(level, 0) < needed
    ]
    if missing_levels:
        print(
            "Not enough questions to satisfy required exam distribution "
            "(2x Level 00, 5x Level 01, 3x Level 02).",
            file=sys.stderr,
        )
        for level in sorted(missing_levels):
            print(
                f"Level {level:02d}: need {QUESTIONS_PER_LEVEL[level]}, "
                f"found {available_per_level.get(level, 0)}",
                file=sys.stderr,
            )
        return 1

    if len(all_questions) < TOTAL_QUESTIONS:
        print(
            f"Not enough questions in Level 00-02. "
            f"Found {len(all_questions)}.",
            file=sys.stderr,
        )
        return 1

    selected = choose_exam_questions(all_questions)
    reset_workdirs()
    seed = int(time.time())
    state = {
        "created_at": seed,
        "seed": seed,
        "current_index": 0,
        "questions": [q.to_dict() for q in selected],
    }
    write_state(state)
    seed_answer_file(state["questions"][0])

    print("Mock exam created: 10 questions (2x L00, 5x L01, 3x L02).")
    print(f"Workspace: {WORK_DIR}")
    print()
    display_question(state)
    return 0


def command_status(_: argparse.Namespace) -> int:
    try:
        state = read_state()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    idx = state["current_index"]
    total = len(state["questions"])
    print(f"Progress: {idx}/{total} solved")
    display_question(state)
    return 0


def command_grade(_: argparse.Namespace) -> int:
    try:
        state = read_state()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    idx = state["current_index"]
    questions = state["questions"]
    if idx >= len(questions):
        print("Exam already completed. Run 'examshell' to start a new one.")
        return 0

    question = questions[idx]
    source_name = Path(question["source_file"]).name
    user_source = ANSWER_DIR / source_name
    if not user_source.exists():
        print(f"Answer file not found: {user_source}", file=sys.stderr)
        return 1

    if question.get("has_main", False):
        ref_bin = BUILD_DIR / "ref.out"
        usr_bin = BUILD_DIR / "user.out"

        ok, log = compile_c(Path(question["source_file"]), ref_bin)
        if not ok:
            print("Internal error: failed to compile reference solution.",
                  file=sys.stderr)
            print(log, file=sys.stderr)
            return 1

        ok, log = compile_c(user_source, usr_bin)
        if not ok:
            print("KO: your code does not compile with -Wall -Wextra -Werror")
            print(log)
            return 1

        ok, log = compare_outputs(ref_bin, usr_bin, state["seed"] + idx)
    else:
        ok, log = compare_function_exercise_outputs(
            Path(question["source_file"]), user_source, question["exercise"]
        )
        if not ok and log.startswith("KO: your code does not compile"):
            lines = log.splitlines()
            print(lines[0])
            if len(lines) > 1:
                print("\n".join(lines[1:]))
            return 1

    if not ok:
        if log.startswith("Internal error"):
            print(log, file=sys.stderr)
            return 1
        print("KO: behavior mismatch")
        print(log)
        return 1

    print(f"OK: {question['exercise']} validated.")
    state["current_index"] += 1
    if state["current_index"] >= len(questions):
        write_state(state)
        print("\nExam completed successfully. Congratulations.")
        return 0

    next_q = questions[state["current_index"]]
    seed_answer_file(next_q)
    write_state(state)
    print()
    display_question(state)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="examshell_engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("start", help="Start a new mock exam")
    subparsers.add_parser("status", help="Show current exam status")
    subparsers.add_parser("grade", help="Grade current answer")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "start":
        return command_start(args)
    if args.command == "status":
        return command_status(args)
    if args.command == "grade":
        return command_grade(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
