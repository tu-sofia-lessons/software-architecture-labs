"""Build the prompt sent to the LLM.

Prompt contract with the model boundary (llm_client.py relies on it). Exactly this shape:

    <instructions: answer only from the context, cite the [source] markers, say when the context
     does not contain the answer>

    CONTEXT:
    [software_architecture.txt | updated 2026-02-01]
    <text of the chunk>
    [exam_rules.txt | updated 2026-02-01]
    <text of the next chunk>

    QUESTION:
    <the question>

    ANSWER:

'CONTEXT:' and 'QUESTION:' must be written exactly like that (capital letters, colon, own line).
"""


def build_prompt(question, chunks):
    # WEEK 09 BUILD: instructions + CONTEXT with a [source | updated date] marker before each chunk + QUESTION.
    raise NotImplementedError("Week 09 Build: implement build_prompt()")
