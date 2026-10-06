# Софтуерни архитектури: упражнения

Кодът за всяко упражнение е в отделен клон: `week-01`, `week-02` и т.н. Клонът се появява в деня на упражнението.

## Веднъж в началото

1. Горе вдясно: **Use this template** → **Create a new repository**.
2. Собственик: вашият профил. Име: `sa-labs-fnXXXXX`. Видимост: **Private**. Отбележете „Include all branches“.
3. **Settings** → **Collaborators** → **Add people** → `igergow`.
4. В новото ви хранилище: **Code** → **Codespaces** → **Create codespace on main**.
5. В Moodle, в заданието „Хранилище за упражненията“, поставете линка към хранилището.

Нищо не се инсталира: нужен е само Python, а той вече е в Codespace-а.

## Всяка седмица

Седмица 1 вече е в хранилището ви: `git switch week-01` и `cd week-01`.

От седмица 2 нататък, в терминала на Codespace-а (за седмица 3 сменете `02` с `03` и т.н.):

```
git remote add upstream https://github.com/tu-sofia-lessons/software-architecture-labs.git   # само първия път
git fetch upstream
git switch -c week-02 upstream/week-02
git push -u origin week-02
cd week-02
```

Работите в клона на седмицата и пазите с `git add`, `git commit`, `git push`. Седмиците са независими: нищо не се пренася от предишната.

## Предаване

С `git commit` и `git push` в клона на седмицата. Броят се вашите commit-и до срока (24 ч след упражнението). При всеки push GitHub пуска проверката на седмицата: вижда се в **Actions**. Подробно: страницата „Как работим по упражненията“ в Moodle.

---

# Software Architecture: labs

The code for each lab is in its own branch: `week-01`, `week-02` and so on. A branch appears on the day of the lab.

## Once, at the start

1. Top right: **Use this template** → **Create a new repository**.
2. Owner: your account. Name: `sa-labs-fnXXXXX`. Visibility: **Private**. Tick "Include all branches".
3. **Settings** → **Collaborators** → **Add people** → `igergow`.
4. In your new repository: **Code** → **Codespaces** → **Create codespace on main**.
5. In Moodle, in the assignment "Lab repository", paste the link to your repository.

Nothing to install: only Python is needed, and the Codespace already has it.

## Every week

Week 1 is already in your repository: `git switch week-01` and `cd week-01`.

From week 2 on, in the Codespace terminal (for week 3 change `02` to `03` and so on):

```
git remote add upstream https://github.com/tu-sofia-lessons/software-architecture-labs.git   # first time only
git fetch upstream
git switch -c week-02 upstream/week-02
git push -u origin week-02
cd week-02
```

You work in the week's branch and save with `git add`, `git commit`, `git push`. The weeks are independent: nothing carries over from the previous one.

## Submission

With `git commit` and `git push` in the week's branch. Your commits up to the deadline count (24 h after the lab). On every push GitHub runs the week's check: see the **Actions** tab. Details: the page "How we work in the labs" in Moodle.
