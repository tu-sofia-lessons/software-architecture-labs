# ADR — template and grading example

::: goal
An **ADR (Architecture Decision Record)** is a short note: what we decided, why, what it costs and when we will revisit it. Up to **150 words**, **4 headings**, no essays. You write it at home within 24 h after the lab and add it to §9 of the architecture document.
:::

## Template

```
# ADR-NNN — <short title>
Week NN · <name> · status: accepted

## Decision
What did we choose? (1–2 sentences)

## Why
Which driver, constraint or quality attribute decided it? Which option did we reject, and why?

## Cost
What became harder, riskier or more expensive? (concrete: what, for whom, when)

## Reconsider when
Which observable change would make us revisit it?
```

## Example: one decision, two grades

A scenario from **another domain**: an online shop calculates delivery in two places — the web checkout and the mobile app.

::: {.note title="Version A — graded 2 of 4"}
**Decision:** We made a module for deliveries.
**Why:** Because it is better and the code is cleaner. It is good practice.
**Cost:** It gets a bit more complex.
**Reconsider when:** If the requirements change.
:::

::: {.check title="Version B — graded 4 of 4"}
**Decision:** The delivery price is calculated only in the module `Shipping.cost(order)`. The web checkout and the mobile API call it and contain no rules of their own.
**Why:** Correctness: the two channels already showed different amounts after a tariff change. Modifiability: tariffs change every month. We rejected "a shared helper function in the UI code", because the next channel (a partner shop) could easily bypass it.
**Cost:** Every channel depends on the signature of `cost()`: if we add a parameter, we touch all three. Scripts that write directly to the database bypass the rules.
**Reconsider when:** Partner systems start creating orders without our code, or deliveries become a separate service with another team.
:::

::: why
**Why is B a 4 and A a 2?**

| Heading | A (weak) | B (strong) |
|---------|----------|------------|
| Decision | doesn't say *what exactly* the module owns | names the owner and what is *not* in the channels |
| Why | "good practice" — not a driver | two drivers from the problem + a rejected option with a reason |
| Cost | "more complex" — cannot be checked | concrete: who, what, when becomes harder |
| Reconsider when | "if it changes" — always true | an observable change someone can notice |
:::
