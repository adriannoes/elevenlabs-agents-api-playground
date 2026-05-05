# Healthcare demo — what to say (fictional)

Use **English** with the configured agent. This file is for reviewers and RAG context only.

## Triage only (no booking)

- Short symptom: "I have had a high fever for two days with a dry cough."
- Escalation probe (should trigger emergency language, not booking): "I have sudden severe chest pain and shortness of breath."

## Happy path for `book_medical_appointment`

The tool expects a **fictional internal reference** `VITA-####` (four digits) and a window **`morning`** or **`afternoon`**. Examples you can speak:

- "My reference is VITA-1001 and I prefer morning."
- "Please book general practice, reference VITA-2044, afternoon."

Do **not** put real CPF, full legal name plus national id, or real medical record numbers into this repository or into chat transcripts you intend to archive.
