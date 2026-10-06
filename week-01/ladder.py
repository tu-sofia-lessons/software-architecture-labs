"""Стълбичката на упражнение 1.

    python ladder.py          покажи стъпалото, на което си, и провери всичко до него
    python ladder.py hint     покажи следващата подсказка за текущото стъпало

Всяко стъпало е ново събитие от бизнеса. Следващото се показва едва когато текущото мине.
Проверката винаги пуска и всички предишни стъпала: поправка, която чупи старо, не се брои.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import csv
import importlib
import json
import re
import shutil
import subprocess
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).parent
STATE_FILE = HERE / ".ladder_state"
sys.path.insert(0, str(HERE))

MIGRATED = "--internal-migrated" in sys.argv       # stage 5 re-runs stages 1-4 on the catalogue's release

# The catalogue team's release, applied by stage 5 to a COPY of the student's code.
# (catalog_update/ holds the same files for reading; the check uses these, so editing that folder changes nothing.)
CATALOG_REPOSITORY = '''"""Data access for courses. SQL about courses lives only here. (Catalogue team, release 2)"""


class CourseRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, course_id):
        row = self.conn.execute(
            "SELECT id, course_code AS code, title, teacher, capacity FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(self):
        rows = self.conn.execute(
            "SELECT id, course_code AS code, title, teacher, capacity FROM courses ORDER BY id")
        return [dict(r) for r in rows]
'''
CATALOG_MIGRATION = '''"""Catalogue team, release 2: migration of the courses table."""


def migrate(conn):
    columns = [r[1] for r in conn.execute("PRAGMA table_info(courses)")]
    if "code" in columns:
        conn.execute("ALTER TABLE courses RENAME COLUMN code TO course_code")
        conn.commit()
'''


# ------------------------------------------------------------------ helpers
def _migrate(conn):
    if MIGRATED:
        importlib.import_module("courses.migration").migrate(conn)


def fresh_db():
    import db
    conn = db.connect(Path(tempfile.mkdtemp()) / "ladder.db")
    _migrate(conn)
    return conn


def fresh_path():
    import db
    path = Path(tempfile.mkdtemp()) / "ladder.db"
    conn = db.connect(path)
    _migrate(conn)
    conn.close()
    return path


def cli_enroll(conn, student_id, course_id):
    import cli
    return cli.enroll_command(conn, student_id, course_id)


def bulk_enroll(conn, *pairs):
    import bulk_enroll
    rows = [{"student_id": str(s), "course_id": str(c)} for s, c in pairs]
    return [(ok, msg) for _, ok, msg in bulk_enroll.run(conn, rows)]


def portal_enroll(conn, student_id, course_id):
    import portal
    return portal.enroll_request(conn, student_id, course_id)


def count(conn, sql, *args):
    return conn.execute(sql, args).fetchone()[0]


def seats(conn, course_id):
    return count(conn, "SELECT COUNT(*) FROM enrollments WHERE course_id = ?", course_id)


def enrolled(conn, student_id, course_id):
    return count(conn, "SELECT COUNT(*) FROM enrollments WHERE student_id = ? AND course_id = ?",
                 student_id, course_id)


# ------------------------------------------------------------------ checks (one per stage)
def check_1():
    conn = fresh_db()
    import bulk_enroll
    with open(HERE / "data" / "bulk.csv", newline="", encoding="utf-8") as f:
        report = bulk_enroll.run(conn, list(csv.DictReader(f)))
    n = seats(conn, 1)
    assert n <= 3, (f"След масовото записване SA101 има {n} студенти, а местата са 3.\n"
                    "Масовото записване още записва в пълен курс.")
    assert all(msg for _, ok, msg in report if not ok), "Всеки отхвърлен ред трябва да казва причината."
    ok, msg = cli_enroll(fresh_db(), 1, 3)
    assert ok, f"CLI спря да записва в свободен курс (Мария в DB150). Отговор: {msg!r}"


def check_2():
    ok_cli, msg_cli = cli_enroll(fresh_db(), 3, 1)
    (ok_bulk, msg_bulk), = bulk_enroll(fresh_db(), (3, 1))
    assert not ok_cli, "Георги НЕ е завършил PR102, но CLI го записа в SA101."
    assert not ok_bulk, "Георги НЕ е завършил PR102, но масовото записване го записа в SA101."
    assert "PR102" in msg_cli, f"Причината за отказа трябва да съдържа PR102. CLI каза: {msg_cli!r}"
    assert msg_cli == msg_bulk, ("Двата канала дават различна причина за един и същ отказ:\n"
                                 f"    CLI:           {msg_cli!r}\n"
                                 f"    масово:        {msg_bulk!r}")
    ok, msg = cli_enroll(fresh_db(), 1, 1)
    assert ok, f"Мария Е завършила PR102, но CLI не я записа в SA101. Отговор: {msg!r}"
    (ok, msg), = bulk_enroll(fresh_db(), (2, 1))
    assert ok, f"Иван Е завършил PR102, но масовото записване не го записа в SA101. Отговор: {msg!r}"


PORTAL_CASES = [
    ("непознат студент: 99 → SA101", [(99, 1)]),
    ("без PR102: Георги → SA101", [(3, 1)]),
    ("пълен курс: трети студент в AI201 (2 места)", [(1, 2), (2, 2), (3, 2)]),
    ("дубликат: Мария → DB150 два пъти", [(1, 3), (1, 3)]),
]


def check_3():
    for name, steps in PORTAL_CASES:
        c_cli, c_portal = fresh_db(), fresh_db()
        for sid, cid in steps[:-1]:                    # the same history on both databases
            cli_enroll(c_cli, sid, cid)
            cli_enroll(c_portal, sid, cid)
        sid, cid = steps[-1]
        ok_c, msg_c = cli_enroll(c_cli, sid, cid)
        before = enrolled(c_portal, sid, cid)
        ok_p, msg_p = portal_enroll(c_portal, sid, cid)
        broke = enrolled(c_portal, sid, cid) > before or seats(c_portal, 2) > 2
        assert not ok_p and not broke, f"Порталът пропусна правило ({name}). Порталът каза: {msg_p!r}"
        assert msg_p == msg_c, (f"Порталът и CLI дават различна причина ({name}):\n"
                                f"    CLI:     {msg_c!r}\n    портал:  {msg_p!r}")
    conn = fresh_db()
    ok, msg = portal_enroll(conn, 1, 3)
    assert ok and enrolled(conn, 1, 3), f"Порталът не записа Мария в DB150, а трябва. Отговор: {msg!r}"


def check_4():
    race = importlib.import_module("race")
    results, n, capacity = race.run(fresh_path())
    crashed = {k: v[1] for k, v in results.items() if v[0] == "CRASH"}
    assert n <= capacity, (f"Двамата служители записаха едновременно и AI201 има {n} студенти, а местата са "
                           f"{capacity}.\nКак е възможно, след като кодът ти проверява местата преди записа?")
    assert not crashed, ("Курсът не се препълни, но единият служител видя грешка (срив) вместо отказ:\n"
                         f"    {crashed}")
    answers = sorted(bool(ok) for ok, _ in results.values())
    assert answers == [False, True], f"Точно един служител трябва да успее. Резултати: {results}"
    rejected = [msg for ok, msg in results.values() if ok is False][0]
    assert "AI201" in rejected, f"Отказът трябва да съдържа името на курса (AI201). Служителят видя: {rejected!r}"


def check_5():
    work = Path(tempfile.mkdtemp()) / "copy"
    shutil.copytree(HERE, work, ignore=shutil.ignore_patterns("__pycache__", "*.db", ".ladder_state"))
    (work / "courses" / "repository.py").write_text(CATALOG_REPOSITORY, encoding="utf-8")
    (work / "courses" / "migration.py").write_text(CATALOG_MIGRATION, encoding="utf-8")
    r = subprocess.run([sys.executable, "ladder.py", "--internal-migrated"], cwd=work,
                       capture_output=True, text=True, timeout=120)
    try:
        result = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        raise AssertionError("Проверката с новото издание не успя да се изпълни:\n" + r.stdout + r.stderr)
    broken = [k for k, v in result.items() if v is not True]
    if broken:
        lines = "\n".join(f"    стъпало {k}: {result[k].strip().splitlines()[-1]}" for k in broken)
        readers = direct_course_readers()
        where = ("\n\nФайлове извън courses/, които четат таблицата courses директно: " + ", ".join(readers)
                 if readers else "")
        raise AssertionError("С новото издание на каталога твоят код се счупи:\n" + lines + where)


def direct_course_readers():
    pattern = re.compile(r"[\"'][^\"'\n]*\b(FROM|JOIN)\s+courses\b", re.IGNORECASE)   # inside an SQL string
    found = []
    for p in sorted(HERE.rglob("*.py")):
        rel = p.relative_to(HERE).as_posix()
        if rel.startswith(("courses/", "catalog_update/")) or rel in ("ladder.py", "db.py", "race.py"):
            continue
        if pattern.search(p.read_text(encoding="utf-8")):
            found.append(rel)
    return found


CHECKS = [check_1, check_2, check_3, check_4, check_5]


# ------------------------------------------------------------------ what the student reads
STAGES = {
1: dict(
    title="Курсът се препълни",
    know="""\
Отговорност е нещо, което кодът решава. Например: „Има ли свободно място в курса?“
Всяко правило живее някъде в кода. На това стъпало ще видиш къде живее това правило.""",
    happened="""\
Учебният отдел пусна масовото записване от файла data/bulk.csv.
Курсът SA101 има 3 места. Записаха се 4 студенти.""",
    see="""\
python cli.py reset
python bulk_enroll.py data/bulk.csv
python cli.py roster 1              ← ще видиш 4 имена""",
    predict="На колко места в кода ще промениш нещо?",
    task="Масовото записване не трябва да записва студент в пълен курс.",
    hints=[
        "Отвори cli.py. Намери функцията enroll_command. Кой ред проверява дали курсът е пълен?",
        "Отвори bulk_enroll.py. Функцията run прави почти същото като enroll_command, но без тази проверка.",
        "Копирай проверката за местата от cli.py в bulk_enroll.py (функцията run), преди INSERT.\n"
        "Ще ти трябва и capacity на курса: добави го в SELECT-а за курса.",
    ]),
2: dict(
    title="Ново правило: предварителен курс",
    know="""\
Свързаност: промяна на едно място те кара да промениш и друго.
  Две копия на едно правило са свързани — смениш ли едното, трябва да смениш и другото.
Модул: част от програмата, която отговаря за едно нещо. Другите части го питат.
Модулен монолит: една програма и една база, но вътре разделена на модули.
  Правило за записване → живее в един модул. CLI и масовото записване → питат модула.""",
    happened="""\
От този семестър в SA101 се записва само който е завършил Програмиране 2 (PR102).
Мария и Иван са завършили PR102. Георги и Елена — не.
Данните вече са в базата: таблиците prerequisites и completed_courses.""",
    see="""\
python cli.py reset
python cli.py enroll 3 1            ← Георги влиза в SA101, а не трябва""",
    predict="Колко файла ще промениш? Как ще си сигурен, че не си пропуснал място?",
    task="""\
Правилото за PR102 трябва да важи и в CLI, и в масовото записване.
Двата канала трябва да дават ЕДНА И СЪЩА причина за отказ, която съдържа PR102.""",
    hints=[
        "prerequisites казва кой курс какво изисква. completed_courses казва кой студент какво е завършил.",
        "Можеш да добавиш проверката на двете места.\n"
        "Или да направиш ЕДНО място с всички правила (папката enrollment/), а двата канала да го питат.\n"
        "Помисли: кое ще е по-лесно, ако утре се появи трета входна точка?",
        "Едно място: enrollment/service.py с функция enroll(...), която проверява всички правила\n"
        "и при нарушение хвърля грешка с причината. cli.py и bulk_enroll.py само я викат и показват причината.",
    ]),
3: dict(
    title="Студентският портал",
    know="""\
Входна точка: мястото, откъдето заявката влиза в системата — CLI, масово записване, уеб портал.
Граница: линията около модула. Вътре са правилата. Отвън другите само го викат.""",
    happened="""\
Екипът на студентския портал ни предаде portal.py. От днес студентите се записват сами.
Отвори portal.py: той записва направо в базата, без никаква проверка.""",
    see="""\
python cli.py reset
python portal.py 3 1                ← Георги влиза в SA101 без PR102""",
    predict="Колко реда с правила ще напишеш в portal.py? Защо точно толкова?",
    task="""\
Порталът трябва да спазва ВСИЧКИ правила (непознат студент или курс, дубликат, места, PR102)
и да дава същите причини като CLI.
Функцията enroll_request остава със същото име и параметри — уеб страницата я вика.""",
    hints=[
        "Какво правят cli.py и bulk_enroll.py, за да спазят правилата? Може ли порталът да направи същото?",
        "Ако правилата ти са в един модул, порталът просто го пита.\n"
        "Ако правилата ти са копирани, трябва да ги копираш и тук, дума по дума.",
        "С модул: в enroll_request извикай модула; при грешка върни (False, причината),\n"
        "иначе (True, съобщение). Това са около 3–5 реда.",
    ]),
4: dict(
    title="Двама служители в една и съща секунда",
    know="""\
Инвариант: правило, което трябва да е вярно ВИНАГИ, за всеки, който пише в базата.
  Пример: „Записаните в курс никога не са повече от местата.“
Базата може сама да пази инвариант (ограничение или тригер).
  Тогава го пази и за код, който още не е написан.""",
    happened="""\
AI201 има 2 места, а в него се оказаха 3 студенти.
Двама служители натиснаха „Запиши“ в една и съща секунда, от два компютъра.
race.py повтаря точно това.""",
    see="""\
python race.py                      ← ще видиш OVERBOOKED""",
    predict="Може ли проверка в Python кода, колкото и да е добра, да спре това? Защо?",
    task="""\
При едновременно записване курсът не трябва да се препълва.
Служителят, който е закъснял, трябва да получи отказ, в който пише AI201 — не грешка (срив).""",
    hints=[
        "И двамата служители питат „Има ли място?“ ПРЕДИ който и да е да е записал. И двамата виждат 1 от 2.",
        "Кой вижда и двете записвания в момента на записа? Базата. Как базата може да откаже запис?",
        "В db.py добави към SCHEMA тригер: CREATE TRIGGER ... BEFORE INSERT ON enrollments,\n"
        "който с RAISE(ABORT, 'course is full') отказва, ако местата са заети.\n"
        "После в Python хвани sqlite3.IntegrityError и върни отказ като \"AI201 is full (2/2)\".",
    ]),
5: dict(
    title="Екипът на каталога издава нова версия",
    know="""\
Собственост върху данните: кой модул има право да чете и променя една таблица.
Модулът courses/ притежава таблицата courses. Другите го питат (CourseService),
а не четат таблицата му директно.""",
    happened="""\
Курсовете вече се поддържат от друг екип — екипът на каталога.
Новото им издание преименува колоната code в таблицата courses на course_code.
Прочети catalog_update/README.md.""",
    see="""\
python ladder.py                    ← проверката сама прилага изданието върху копие на кода ти""",
    predict="Кои от твоите файлове четат таблицата courses директно? Какво ще им се случи?",
    task="""\
След новото издание твоят код трябва да продължи да работи.
Не пипай кода на каталога (courses/, catalog_update/). Ако нещо се счупи, поправи СВОЯ код.""",
    hints=[
        "Потърси SQL, който чете courses:  grep -n \"courses\" *.py   (Windows: findstr /n courses *.py)",
        "cli.py вече пита CourseService за курса. Кой друг файл чете таблицата courses сам?",
        "Замени директния SQL към courses с CourseService(CourseRepository(conn)).get_course(course_id).\n"
        "Той връща code и capacity и след новото издание.",
    ]),
}

DONE = """\
Изкачи и петте стъпала.

Последно, на картата:
  1. Попълни реда за стила на седмицата:
       Модулен монолит · какво решава · какво струва · кога е грешният избор
  2. Кое стъпало те научи на най-много и защо?"""


# ------------------------------------------------------------------ state and output
def load_state():
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {"seen": set(data.get("seen", [])), "hints": {int(k): v for k, v in data.get("hints", {}).items()}}
    except (OSError, ValueError):
        return {"seen": set(), "hints": {}}


def save_state(state):
    try:
        STATE_FILE.write_text(json.dumps({"seen": sorted(state["seen"]), "hints": state["hints"]}), encoding="utf-8")
    except OSError:
        pass


def run_check(fn):
    try:
        fn()
        return True
    except AssertionError as e:
        return str(e)
    except Exception:
        return "Кодът ти се срина:\n" + traceback.format_exc(limit=3)


def indent(text):
    return "\n".join("  " + line if line else "" for line in text.splitlines())


def show_stage(stage, result):
    s = STAGES[stage]
    print(f"\n━━━━━━━━  Стъпало {stage} от {len(CHECKS)} · {s['title']}  ━━━━━━━━\n")
    print("ЗНАЙ\n" + indent(s["know"]) + "\n")
    print("КАКВО СЕ СЛУЧИ\n" + indent(s["happened"]) + "\n")
    print("ВИЖ ГО САМ\n" + indent(s["see"]) + "\n")
    print(f"ПРЕДВИДИ — запиши на картата, ред {stage}, ПРЕДИ да пипнеш кода\n  " + s["predict"] + "\n")
    print("ЗАДАЧА\n" + indent(s["task"]) + "\n")
    print("ГОТОВО Е, КОГАТО\n  python ladder.py  покаже  ✓ Стъпало " + str(stage) + "\n")
    print("ЗАСЯДАШ ЛИ?\n  python ladder.py hint\n")
    print("─── Проверката казва ───")
    if result is True:
        print(indent("✓ Кодът ти вече издържа това — без нито една промяна.\n"
                     "На картата, ред " + str(stage) + ": ЗАЩО? Кое твое решение от предишните стъпала го направи?"))
    else:
        print(indent(result))
    print("\nКогато си готов: python ladder.py")


def current_stage(state, quiet=False):
    """The first stage that fails or has never been shown. Returns (stage, result) or (None, None)."""
    for stage, fn in enumerate(CHECKS, 1):
        result = run_check(fn)
        if result is not True or stage not in state["seen"]:
            return stage, result
        if not quiet:
            print(f"✓ Стъпало {stage} · {STAGES[stage]['title']}")
    return None, None


def main():
    if MIGRATED:
        print(json.dumps({str(i): run_check(fn) for i, fn in enumerate(CHECKS[:4], 1)}, ensure_ascii=False))
        return 0
    if "--json" in sys.argv:                           # for the course authors' validation
        print(json.dumps({str(i): run_check(fn) for i, fn in enumerate(CHECKS, 1)}, ensure_ascii=False))
        return 0

    state = load_state()
    wants_hint = len(sys.argv) > 1 and sys.argv[1] == "hint"
    stage, result = current_stage(state, quiet=wants_hint)
    if stage is None:
        print("\n━━━━━━━━  Готово  ━━━━━━━━\n")
        print(DONE)
        return 0

    if wants_hint:
        hints = STAGES[stage]["hints"]
        level = min(state["hints"].get(stage, 0) + 1, len(hints))
        state["hints"][stage] = level
        save_state(state)
        print(f"\nПодсказка {level} от {len(hints)} · стъпало {stage} · {STAGES[stage]['title']}\n")
        print(indent(hints[level - 1]))
        if level < len(hints):
            print("\nОще една подсказка: python ladder.py hint")
        return 0

    state["seen"].add(stage)
    save_state(state)
    show_stage(stage, result)
    return 0 if result is True else 1


if __name__ == "__main__":
    sys.exit(main())
