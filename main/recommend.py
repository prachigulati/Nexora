import os
import re
from main.ai_service import ai_service

def gemini_compare(projects):
    """
    Compares startups and returns structured suggestions + scores.
    """

    # Prepare startup info for the prompt
    project_info = []
    for p in projects:
        project_info.append(
            f"Startup: {p.name}\n"
            f"Description: {p.description or 'N/A'}\n"
            f"Problem: {p.problem or 'N/A'}\n"
            f"Market: {p.market or 'N/A'}\n"
            f"Competition: {p.competition or 'N/A'}\n"
        )

    prompt = f"""
You are an AI startup advisor. Compare the following startups.

{chr(10).join(project_info)}

Instructions:
- For each startup, assign a score (0-100) for:
  Market, Problem, Competition, Risks.
- Provide short notes for each startup.
- At the end, recommend the most promising startup with reason.
- Optionally, provide a confidence % for your recommendation.
- Output in strict format:

[START]
Startup1: Name
Market: <score>
Problem: <score>
Competition: <score>
Risks: <score>
Notes: <short text>

Startup2: Name
Market: <score>
Problem: <score>
Competition: <score>
Risks: <score>
Notes: <short text>

Recommendation: <startup name>
Reason: <short text>
Confidence: <number>
[END]
"""

    response = ai_service.generate_content(prompt, max_tokens=1000)
    text = response.strip()
    text = text.replace("[END]", "").strip()

    data = {"analysis": {}, "recommendation": {}}

    # Helper to extract numeric score from any string
    def extract_score(val):
        match = re.search(r'\d+', val)
        return int(match.group()) if match else 0

    try:
        # Robust startup block parsing (handles "Startup 1:" or "Startup1:")
        startup_blocks = re.findall(
            r'(Startup\s*\d*\s*:\s*.+?)(?=Startup\s*\d*\s*:|Recommendation:|$)',
            text, re.DOTALL
        )

        for block in startup_blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue

            name = lines[0].split(":", 1)[1].strip()
            scores = {"Market": 0, "Problem": 0, "Competition": 0, "Risks": 0}
            notes = "No notes available."

            for line in lines[1:]:
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key, val = key.strip(), val.strip()
                if key in scores:
                    scores[key] = extract_score(val)
                elif key.lower() == "notes":
                    notes = val

            data["analysis"][name] = {"scores": scores, "notes": notes}

        # Recommendation parsing
        rec_match = re.search(r'Recommendation:\s*(.+)', text)
        reason_match = re.search(r'Reason:\s*(.+)', text)
        conf_match = re.search(r'Confidence:\s*(\d+)', text)

        data["recommendation"]["name"] = rec_match.group(1).strip() if rec_match else "N/A"
        data["recommendation"]["reason"] = reason_match.group(1).strip() if reason_match else "No reason provided."
        data["recommendation"]["confidence"] = int(conf_match.group(1)) if conf_match else 0

    except Exception as e:
        data["error"] = f"Parsing failed: {str(e)}"
        data["raw"] = text

    return data