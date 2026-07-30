# 🚀 [Tips Hindawi](https://www.tipshindawi.com/) Challenge (June–July) 2026

> 🏆 This repository is my official submission for the [ **Tips Hindawi** ](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

## 👤 Participant

| Field            | Value                                |
| ---------------- | ------------------------------------ |
| Full Name        | Youssef Ehab Abdo Gomaa                                     |
| Project Name     | Resufit                                     |
| GitHub Username  | youssefgomaa7                                     |
| Challenge Batch  | June–July 2026                       |
| Training Program | Large Language Models (LLMs) Program |
| Organization     | [**Edrak for Ai**](https://edrak4ai.com/en)                         |

---

# 📖 Project Overview

**ResuFit** is an AI-powered resume optimizer and ATS (Applicant Tracking System) match evaluator. You upload your CV and paste a target job description, and ResuFit tells you exactly how well your resume matches the role — then rewrites it to close the gap.

Under the hood, it works like a "review desk": a deterministic **ATS scoring engine** (TF-IDF weighted keyword coverage) grades your CV against the job description, identifies the highest-value keywords you're missing, and hands that gap analysis to a **self-hosted LLM** (Mistral-Nemo-Instruct, running on a free Kaggle GPU and exposed via ngrok) that rewrites your CV, transforms weak bullet points into achievement-driven ones, and generates an elevator pitch plus likely interview questions — all while flagging any numbers the model may have hallucinated so you never submit a fabricated stat by mistake.

---

# ✨ Features

 **Weighted ATS Match Score** — TF-IDF-based keyword coverage score (0–100%) comparing your CV against the job description, before and after optimization, with a visible score gain.
 **Keyword Gap Analysis** — surfaces the highest-importance keywords/phrases missing from your CV, and shows which of them were successfully integrated vs. still need real candidate input.
 **AI-Powered CV Rewrite** — rewrites your full CV to naturally weave in missing keywords, while strictly preserving your original section names, order, and content (no generic re-templating, no dropped sections).
 **Bullet Point Transformations** — shows a clear before → after view of how raw experience statements were rewritten into stronger, keyword-optimized achievement bullets.
 **Hallucination Guardrail** — cross-checks every number in the optimized CV and bullets against your original CV, and flags any unverified figures the model introduced so you can confirm them before using them.
 **Elevator Pitch & Interview Prep** — generates a tailored 30-second pitch and a set of likely interview questions based on the role.
 **Robust LLM Output Parsing** — multi-strategy JSON extraction (direct parse → repair → regex fallback → raw-document salvage) so a malformed model response never silently produces a blank or broken result.
 **"Review Desk" UI** — a custom Streamlit theme styled like a document being reviewed on a desk, with ink-stamp score cards, keyword badges, and folder-tab navigation across Overview, Optimized CV, Bullet Transformations, and Pitch & Interview Prep.

---

# 🛠️ Technologies Used

 **Frontend / App:** [Streamlit](https://streamlit.io/) (custom CSS theming), `pypdf` for CV PDF parsing
 **LLM Orchestration:** [LangChain](https://www.langchain.com/) (custom `BaseChatModel` wrapper)
 **LLM Serving:** [Mistral-Nemo-Instruct-2407](https://huggingface.co/mistralai/Mistral-Nemo-Instruct-2407) via 🤗 `transformers`, hosted on a Kaggle notebook (T4 GPU) and exposed publicly through **FastAPI + ngrok**
 **ATS Scoring:** `scikit-learn` (`TfidfVectorizer`) for weighted keyword extraction and coverage scoring
 **Validation / Parsing:** `pydantic` for structured LLM output, `re` for JSON repair and salvage strategies
 **Config:** `python-dotenv` for environment variable management

---

# ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/youssefgomaa7/resufit
   cd resufit
   ```

2. **Install dependencies**
   ```bash
   pip install streamlit pypdf python-dotenv langchain-core pydantic requests scikit-learn
   ```

3. **Start the LLM backend on Kaggle**
   * Open `ngrok-llm.ipynb` in a Kaggle notebook with GPU (T4) enabled and internet access turned on.
   * Set your own **ngrok auth token** and a private **API key** in the notebook (do **not** reuse any token that has ever been committed or shared — treat it as compromised and generate a fresh one).
   * Run all cells. The notebook loads `Mistral-Nemo-Instruct-2407`, spins up a FastAPI `/generate` endpoint, and tunnels it through ngrok, printing a public URL like `https://<random>.ngrok-free.dev`.

4. **Configure the app**
   Create a `.env` file in the project root:
   ```
   NGROK_URL=https://<your-ngrok-subdomain>.ngrok-free.dev
   NGROK_API_KEY=<the API key you set in the notebook>
   ```

5. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

---

# 🚀 Usage

1. Launch the app and upload your CV (PDF) or paste its text.
2. Paste the target job description.
3. Click the optimize/submit button to run the pipeline — ResuFit scores your original CV, identifies missing high-value keywords, and sends everything to the LLM for rewriting.
4. Explore the results across four tabs:
   * **Overview** — before/after ATS match score, net score gain, and keyword gap analysis.
   * **Optimized CV** — the complete rewritten CV, ready to copy or download as `.txt`.
   * **Bullet Transformations** — side-by-side before/after view of individual rewritten bullets, with hallucination warnings where relevant.
   * **Pitch & Interview Prep** — a tailored elevator pitch and likely interview questions for the role.
5. Review any flagged "unverified numbers" or "still open" keywords before using the optimized CV — these need your manual confirmation, since the AI won't fabricate experience but may need help mapping abstract JD keywords onto your real background.


# 🔮 Future Improvements

* Swap the Kaggle + ngrok LLM hosting for a more stable, always-on inference endpoint (e.g. a hosted API or persistent GPU instance) so the app doesn't depend on an active notebook session.
* Support multiple CV input formats (DOCX, plain text paste) alongside PDF.
* Add multi-job-description comparison to see how one CV scores across several target roles at once.
* Persist optimization history so users can track score improvements over time.

---

# 📚 About the Challenge

This project was developed as part of the [**Tips Hindawi**](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

[Tips Hindawi](https://www.tipshindawi.com/) is the internships department of [**Edrak for Ai**](https://edrak4ai.com/en), and the challenge encourages participants to build real-world projects, apply practical skills, and showcase their work through GitHub.

For more information about the challenge, training programs, and upcoming batches, visit the official [Tips Hindawi](https://www.tipshindawi.com/) website.

---

# 📄 License

This project is shared for educational and portfolio purposes.
