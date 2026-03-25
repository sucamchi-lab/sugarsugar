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

    def to_dict(self) -> Dict[str, str]:
        return {
            "level": self.level,
            "bucket": self.bucket,
            "exercise": self.exercise,
            "exercise_dir": str(self.exercise_dir),
            "source_file": str(self.source_file),
            "subject_file": str(self.subject_file),
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
            if not has_main_function(source_file):
                continue

            questions.append(
                Question(
                    level=level,
                    bucket=bucket,
                    exercise=entry.name,
                    exercise_dir=entry,
                    source_file=source_file,
                    subject_file=subject_file,
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
    cmd = [
        "gcc",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(source),
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
            f"Not enough questions with a main function in Level 00-02. "
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

    ref_bin = BUILD_DIR / "ref.out"
    usr_bin = BUILD_DIR / "user.out"

    ok, log = compile_c(Path(question["source_file"]), ref_bin)
    if not ok:
        print("Internal error: failed to compile reference solution.", file=sys.stderr)
        print(log, file=sys.stderr)
        return 1

    ok, log = compile_c(user_source, usr_bin)
    if not ok:
        print("KO: your code does not compile with -Wall -Wextra -Werror")
        print(log)
        return 1

    ok, log = compare_outputs(ref_bin, usr_bin, state["seed"] + idx)
    if not ok:
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
