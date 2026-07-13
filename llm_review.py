import os
import re
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_diff_with_line_numbers(patch: str) -> str:
    """Walks a unified diff and annotates each surviving line with its real line number in the new file."""
    if not patch:
        return ""
    lines = patch.split("\n")
    annotated = []
    new_line_num = None
    for line in lines:
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                new_line_num = int(match.group(1))
            continue  # skip hunk headers in the annotated output, they're just bookkeeping
        if line.startswith("-"):
            continue  # removed line — doesn't exist in the new file, nothing to annotate
        elif line.startswith("+"):
            annotated.append(f"{new_line_num}: + {line[1:]}")
            new_line_num += 1
        else:
            annotated.append(f"{new_line_num}:   {line[1:] if line.startswith(' ') else line}")
            new_line_num += 1
    return "\n".join(annotated)

def build_prompt(filename: str, annotated_diff: str) -> str:
    return f"""You are reviewing a code change in `{filename}`. Below is the diff, with each surviving line annotated with its real line number in the new version of the file. Lines marked with `+` were added or changed in this PR; unmarked lines are unchanged context shown only for reference.

    Review ONLY the `+` lines. Do not comment on style, formatting, naming, or anything a linter would already catch. Focus only on: unclear logic, missing edge-case handling (null/empty/error cases), race conditions, or genuine bugs a careful human reviewer would flag.

    If there are no real issues, return an empty array. Do not invent issues to have something to say.

    Diff:
    {annotated_diff}

    Respond with ONLY a JSON array, no explanation, no markdown fences, in this exact format:
    [{{"line": <int>, "severity": "low"|"medium"|"high", "comment": "<specific, actionable feedback>"}}]
    """


def call_llm_review(filename: str, patch: str):
    annotated = parse_diff_with_line_numbers(patch)
    if not annotated:
        return []

    prompt = build_prompt(filename, annotated)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()

    # strip markdown code fences if the model added them despite instructions
    if raw.startswith("```"):
        raw = re.sub(r"^```(json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        issues = json.loads(raw)
    except json.JSONDecodeError:
        print(f"    [llm error] unparseable response for {filename}: {raw[:200]}", flush=True)
        return []

    return [i for i in issues if i.get("severity") in ("medium", "high")]