# Софтуерни архитектури: упражнения

Кодът за всяко упражнение е в отделен клон: `week-01`, `week-02` и т.н. Клонът се появява в деня на упражнението.

## Веднъж в началото

1. Горе вдясно: **Use this template** → **Create a new repository**.
2. Собственик: вашият профил. Видимост: **Private**. Не отбелязвайте „Include all branches“.
3. В новото ви хранилище: **Code** → **Codespaces** → **Create codespace on main**.

Нищо не се инсталира: нужен е само Python, а той вече е в Codespace-а.

## Всяка седмица

В терминала на Codespace-а (за седмица 2 сменете `01` с `02` и т.н.):

```
git remote add upstream https://github.com/tu-sofia-lessons/software-architecture-labs.git   # само първия път
git fetch upstream
git switch -c week-01 upstream/week-01
git push -u origin week-01
cd week-01
python ladder.py
```

Работите в клона на седмицата и пазите с `git add`, `git commit`, `git push`. Седмиците са независими: нищо не се пренася от предишната.

## Предаване

Свалете папката на седмицата като zip с име `fnXXXXX_wNN.zip` (вашият факултетен номер и седмицата) и го качете в Moodle. В Codespace: десен бутон върху папката → **Download...**

---

# Software Architecture: labs

The code for each lab is in its own branch: `week-01`, `week-02` and so on. A branch appears on the day of the lab.

## Once, at the start

1. Top right: **Use this template** → **Create a new repository**.
2. Owner: your account. Visibility: **Private**. Do not tick "Include all branches".
3. In your new repository: **Code** → **Codespaces** → **Create codespace on main**.

Nothing to install: only Python is needed, and the Codespace already has it.

## Every week

In the Codespace terminal (for week 2 change `01` to `02` and so on):

```
git remote add upstream https://github.com/tu-sofia-lessons/software-architecture-labs.git   # first time only
git fetch upstream
git switch -c week-01 upstream/week-01
git push -u origin week-01
cd week-01
python ladder.py
```

You work in the week's branch and save with `git add`, `git commit`, `git push`. The weeks are independent: nothing carries over from the previous one.

## Submission

Download the week's folder as a zip named `fnXXXXX_wNN.zip` (your faculty number and the week) and upload it to Moodle. In the Codespace: right-click the folder → **Download...**
