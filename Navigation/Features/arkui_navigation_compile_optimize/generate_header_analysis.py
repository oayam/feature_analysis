#!/usr/bin/env python3
import argparse
import json
import math
import re
import shlex
from collections import Counter, OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


ZERO_OPTIMIZED = "直接删除"
LITTLE_OPTIMIZED = "优先尝试前向声明；如存在内联实现或模板/constexpr依赖，则将实际调用移动到cpp"
MANY_OPTIMIZED = "不建议直接删除；优先考虑缩小包含范围、拆分更轻量头文件或减少传递包含"

KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept",
    "const", "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await",
    "co_return", "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
    "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq",
    "nullptr", "operator", "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "requires", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template", "this", "thread_local",
    "throw", "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
}

CONTROL_WORDS = {"if", "for", "while", "switch", "catch", "return", "sizeof"}

CLASS_LIKE_RE = re.compile(r"\b(?:class|struct|union|enum(?:\s+class)?)\s+([A-Za-z_]\w*)")
USING_ALIAS_RE = re.compile(r"\busing\s+([A-Za-z_]\w*)\s*=")
USING_IMPORT_RE = re.compile(r"\busing\s+(?:[A-Za-z_]\w*::)+([A-Za-z_]\w*)\s*;")
TYPEDEF_RE = re.compile(r"\btypedef\b[^;{}()]*?\b([A-Za-z_]\w*)\s*;")
MACRO_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)", re.MULTILINE)
IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^">]+\.h)[>"]', re.MULTILINE)


@dataclass
class CompileEntry:
    directory: Path
    command: str
    include_dirs: List[Path]
    quote_dirs: List[Path]


def strip_comments_and_strings(text: str) -> str:
    result: List[str] = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < length else ""
        if ch == "/" and nxt == "/":
            i += 2
            while i < length and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < length and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if ch in {"'", '"'}:
            quote = ch
            result.append(" ")
            i += 1
            while i < length:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def load_owner_files(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return sorted(
        file_name
        for file_name, meta in data.items()
        if "@arkui_navigation" in meta.get("owners", [])
    )


def parse_include_dirs(command: str, directory: Path) -> Tuple[List[Path], List[Path]]:
    tokens = shlex.split(command)
    include_dirs: List[Path] = []
    quote_dirs: List[Path] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        value: Optional[str] = None
        target: Optional[List[Path]] = None
        if token in {"-I", "-isystem", "-iquote"}:
            if i + 1 < len(tokens):
                value = tokens[i + 1]
                target = quote_dirs if token == "-iquote" else include_dirs
                i += 1
        elif token.startswith("-I") and token != "-I":
            value = token[2:]
            target = include_dirs
        elif token.startswith("-isystem") and token != "-isystem":
            value = token[len("-isystem") :]
            target = include_dirs
        elif token.startswith("-iquote") and token != "-iquote":
            value = token[len("-iquote") :]
            target = quote_dirs
        if value and target is not None:
            candidate = (directory / value).resolve() if not Path(value).is_absolute() else Path(value)
            target.append(candidate)
        i += 1
    return include_dirs, quote_dirs


def load_compile_entries(path: Path, owner_files: Sequence[str]) -> Dict[str, CompileEntry]:
    targets = {"../../" + file_name: file_name for file_name in owner_files}
    results: Dict[str, CompileEntry] = {}
    current_file: Optional[str] = None
    current_dir: Optional[Path] = None
    current_command: Optional[str] = None
    file_re = re.compile(r'^\s*"file":\s*"([^"]+)"')
    dir_re = re.compile(r'^\s*"directory":\s*"([^"]+)"')
    cmd_re = re.compile(r'^\s*"command":\s*"(.*)"')
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            file_match = file_re.match(line)
            if file_match:
                raw_file = file_match.group(1)
                current_file = targets.get(raw_file)
                current_dir = None
                current_command = None
                continue
            if current_file is None:
                continue
            dir_match = dir_re.match(line)
            if dir_match:
                current_dir = Path(dir_match.group(1))
                continue
            cmd_match = cmd_re.match(line)
            if cmd_match:
                current_command = json.loads('"' + cmd_match.group(1) + '"')
                if current_dir is None:
                    continue
                include_dirs, quote_dirs = parse_include_dirs(current_command, current_dir)
                results[current_file] = CompileEntry(
                    directory=current_dir,
                    command=current_command,
                    include_dirs=include_dirs,
                    quote_dirs=quote_dirs,
                )
                current_file = None
                current_dir = None
                current_command = None
                if len(results) == len(owner_files):
                    break
    return results


def extract_includes(source_text: str) -> List[str]:
    return [match.group(1) for match in INCLUDE_RE.finditer(source_text)]


def extract_symbols(header_text: str) -> Set[str]:
    stripped = strip_comments_and_strings(header_text)
    symbols: Set[str] = set()
    for regex in (CLASS_LIKE_RE, USING_ALIAS_RE, USING_IMPORT_RE, TYPEDEF_RE, MACRO_RE):
        symbols.update(match.group(1) for match in regex.finditer(stripped))
    return {symbol for symbol in symbols if symbol not in KEYWORDS and not symbol.startswith("_")}


def threshold_for_lines(line_count: int) -> int:
    return max(1, min(10, math.ceil(max(line_count, 1) / 50)))


def build_search_dirs(source_path: Path, compile_entry: Optional[CompileEntry]) -> List[Path]:
    dirs: List[Path] = [source_path.parent]
    if compile_entry is None:
        return dirs
    for path in compile_entry.quote_dirs + compile_entry.include_dirs:
        if path not in dirs:
            dirs.append(path)
    return dirs


def resolve_header(
    include_name: str,
    search_dirs: Sequence[Path],
    repo_root: Path,
    basename_index: Dict[str, List[Path]],
) -> Optional[Path]:
    include_path = Path(include_name)
    for base in search_dirs:
        candidate = (base / include_name).resolve()
        if candidate.is_file():
            return candidate
    repo_candidate = (repo_root / include_name).resolve()
    if repo_candidate.is_file():
        return repo_candidate
    basename = include_path.name
    candidates = basename_index.get(basename, [])
    if not candidates:
        return None
    if include_name.count("/"):
        suffix_matches = [path for path in candidates if str(path).endswith(include_name)]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
        if suffix_matches:
            candidates = suffix_matches
    return sorted(candidates, key=lambda path: (len(path.parts), str(path)))[0]


def build_basename_index(repo_root: Path) -> Dict[str, List[Path]]:
    index: Dict[str, List[Path]] = {}
    for path in repo_root.rglob("*.h"):
        index.setdefault(path.name, []).append(path.resolve())
    return index


def analyze_file(
    file_name: str,
    repo_root: Path,
    compile_entry: Optional[CompileEntry],
    basename_index: Dict[str, List[Path]],
    symbol_cache: Dict[Path, Set[str]],
) -> OrderedDict:
    source_path = repo_root / file_name
    if not source_path.is_file():
        return OrderedDict(
            [
                ("0_used_headers", []),
                ("little_used_headers", []),
                ("many_times_used_headers", []),
            ]
        )
    raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    stripped = strip_comments_and_strings(raw_text)
    identifiers = Counter(IDENT_RE.findall(stripped))
    includes = extract_includes(raw_text)
    threshold = threshold_for_lines(raw_text.count("\n") + 1)
    search_dirs = build_search_dirs(source_path, compile_entry)
    resolved_cache: Dict[str, Optional[Path]] = {}

    zero_used_headers: List[Dict[str, object]] = []
    little_used_headers: List[Dict[str, object]] = []
    many_times_used_headers: List[Dict[str, object]] = []

    for include_name in includes:
        if include_name not in resolved_cache:
            resolved_cache[include_name] = resolve_header(include_name, search_dirs, repo_root, basename_index)
        header_path = resolved_cache[include_name]
        symbols: Set[str] = set()
        if header_path is not None and header_path.is_file():
            symbols = symbol_cache.get(header_path)
            if symbols is None:
                header_text = header_path.read_text(encoding="utf-8", errors="ignore")
                symbols = extract_symbols(header_text)
                symbol_cache[header_path] = symbols
        used_count = sum(identifiers[symbol] for symbol in symbols)
        if used_count == 0:
            zero_used_headers.append({"file_name": include_name, "optimized": ZERO_OPTIMIZED})
        elif used_count < threshold:
            little_used_headers.append(
                {
                    "file_name": include_name,
                    "used_count": used_count,
                    "optimized": LITTLE_OPTIMIZED,
                }
            )
        else:
            many_times_used_headers.append(
                {
                    "file_name": include_name,
                    "used_count": used_count,
                    "optimized": MANY_OPTIMIZED,
                }
            )
    little_used_headers.sort(key=lambda item: (item["used_count"],))
    many_times_used_headers.sort(key=lambda item: (item["used_count"],))
    return OrderedDict(
        [
            ("0_used_headers", zero_used_headers),
            ("little_used_headers", little_used_headers),
            ("many_times_used_headers", many_times_used_headers),
        ]
    )


def entry_line_count(file_name: str, payload: OrderedDict) -> int:
    text = json.dumps({file_name: payload}, ensure_ascii=False, indent=2)
    return text.count("\n") + 1


def write_parts(output_dir: Path, results: List[Tuple[str, OrderedDict]], max_lines: int) -> List[Path]:
    paths: List[Path] = []
    current: OrderedDict[str, OrderedDict] = OrderedDict()
    current_lines = 2
    part = 1
    for file_name, payload in results:
        lines = entry_line_count(file_name, payload)
        extra = lines if not current else lines - 2
        if current and current_lines + extra > max_lines:
            part_path = output_dir / f"result_part_{part}.json"
            part_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            paths.append(part_path)
            current = OrderedDict()
            current_lines = 2
            part += 1
        current[file_name] = payload
        current_lines += lines if len(current) == 1 else lines - 2
    if current:
        part_path = output_dir / f"result_part_{part}.json"
        part_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(part_path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate arkui_navigation header analysis result.")
    parser.add_argument("--repo-root", default=".", help="Workspace root")
    parser.add_argument(
        "--owner-mapping",
        default="feature_analysis/Navigation/Features/arkui_navigation_compile_optimize/owner_mapping.json",
        help="owner_mapping.json path",
    )
    parser.add_argument(
        "--compile-commands",
        default="out/rk3568/compile_commands.json",
        help="compile_commands.json path",
    )
    parser.add_argument(
        "--output-root",
        default="feature_analysis/Navigation/Features/arkui_navigation_compile_optimize/header_analysis_result",
        help="Output directory root",
    )
    parser.add_argument("--max-lines", type=int, default=10000, help="Max lines for each split json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    owner_mapping = (repo_root / args.owner_mapping).resolve()
    compile_commands = (repo_root / args.compile_commands).resolve()
    output_root = (repo_root / args.output_root).resolve()

    owner_files = load_owner_files(owner_mapping)
    compile_entries = load_compile_entries(compile_commands, owner_files)
    basename_index = build_basename_index(repo_root)
    symbol_cache: Dict[Path, Set[str]] = {}
    results: List[Tuple[str, OrderedDict]] = []
    for index, file_name in enumerate(owner_files, start=1):
        payload = analyze_file(file_name, repo_root, compile_entries.get(file_name), basename_index, symbol_cache)
        results.append((file_name, payload))
        if index % 100 == 0:
            print(f"analyzed {index}/{len(owner_files)}")

    output_dir = output_root / datetime.now().strftime("result_%y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=False)
    parts = write_parts(output_dir, results, args.max_lines)

    summary = {
        "output_dir": str(output_dir),
        "files": len(owner_files),
        "compile_entries": len(compile_entries),
        "parts": len(parts),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
