"""
output_files.py — куди навичка складає файли, які створює.

Усе, що створюють скрипти (кошик, перегляди, аналіз, графік, звіт), лягає в
одну теку результатів — типово `wikipedia-interest-output/` у робочій теці —
по підтеці на кожен запуск: `<дата-час>-<QID>/`. У теці результатів навичка
сама створює `.gitignore` (`*`), тож у git ці файли не потрапляють, і нічого
не з'являється поруч із кодом користувача.

Інше місце — змінна середовища WIKIPEDIA_INTEREST_OUTPUT або явний `--out`.
"""

import datetime as dt
import os
from pathlib import Path

OUTPUT_ENV_VAR = "WIKIPEDIA_INTEREST_OUTPUT"
DEFAULT_DIR_NAME = "wikipedia-interest-output"
SKILL_DIR = Path(__file__).resolve().parent.parent
GITIGNORE_TEXT = ("# Файли, які створює навичка wikipedia-interest-analysis (кошики, перегляди, аналіз,\n"
                  "# графіки, звіти). У git не потрапляють; видаляти можна будь-коли.\n*\n")
FILES_HEADING = "Створено теку з результатами:"
FILE_DESCRIPTIONS = {
    "basket.json": "кошик статей (етап 1)",
    "views.json": "перегляди по місяцях чи днях (етап 2)",
    "analysis.json": "аналіз тренду й довіри (етап 3)",
    "views.svg": "графік (етап 3)",
    "report.pdf": "звіт на одну сторінку (етап 4)",
}


def _repo_root(start: Path):
    for d in [start, *start.parents]:
        if (d / ".git").exists():
            return d
    return None


def output_root() -> Path:
    """Тека результатів: змінна середовища, інакше робоча тека. Якщо агент запустив
    скрипт з теки самої навички, результати не повинні лягти поруч із кодом навички."""
    env = os.environ.get(OUTPUT_ENV_VAR, "").strip()
    if env:
        return Path(env)
    cwd = Path.cwd().resolve()
    if cwd == SKILL_DIR or SKILL_DIR in cwd.parents:
        repo = _repo_root(SKILL_DIR)
        base = repo if repo and repo != SKILL_DIR else Path.home()
        return base / DEFAULT_DIR_NAME
    return cwd / DEFAULT_DIR_NAME


def ensure_output_root(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(GITIGNORE_TEXT, encoding="utf-8")
    return root


def new_run_dir(tag: str, now=None) -> Path:
    """Нова підтека запуску, напр. `20260927-145210-Q333`."""
    root = ensure_output_root(output_root())
    stamp = (now or dt.datetime.now()).strftime("%Y%m%d-%H%M%S")
    safe = "".join(c for c in tag if c.isalnum() or c in "-_") or "run"
    run = root / f"{stamp}-{safe}"
    n = 2
    while run.exists():
        run = root / f"{stamp}-{safe}-{n}"
        n += 1
    run.mkdir()
    return run


def run_dir_for(input_path, tag: str) -> Path:
    """Тека для наступного файлу: та сама підтека запуску, якщо вхідний файл уже в ній,
    інакше — нова підтека (щоб не писати поруч із чужими файлами)."""
    parent = Path(input_path).resolve().parent
    marker = parent.parent / ".gitignore"
    if marker.exists() and marker.read_text(encoding="utf-8").startswith(GITIGNORE_TEXT.splitlines()[0]):
        return parent
    return new_run_dir(tag)


def display(path) -> str:
    """Шлях для показу: відносно робочої теки, якщо файл усередині неї."""
    path = Path(path).resolve()
    try:
        return str(path.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def script(name: str) -> str:
    return display(SKILL_DIR / "scripts" / name)


def files_block(run_dir, will_create=()) -> str:
    """Перелік створених файлів запуску — для кінця відповіді користувачу."""
    run_dir = Path(run_dir)
    present = [(n, d) for n, d in FILE_DESCRIPTIONS.items() if (run_dir / n).exists() or n in will_create]
    if not present:
        return ""
    lines = [f"{FILES_HEADING} {run_dir.resolve()}/", "У ній:"]
    lines += [f"- {name} — {desc}" for name, desc in present]
    lines.append(f"(Тека {run_dir.resolve().parent.name}/ має власний .gitignore, тож у git ці файли не потрапляють.)")
    return "\n".join(lines)
