"""
Milestone 5 - Gradio interface for The Unofficial Guide (r/NEU survival guide).

Run:  python app.py   ->  open http://localhost:7860
"""

import gradio as gr

from query import ask


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"- {s}" for s in result["sources"])
    if not sources:
        sources = "(no sources - the documents don't cover this)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# The Unofficial Guide - r/NEU Survival Guide\n"
        "Ask about surviving Northeastern. Answers come **only** from student-written "
        "r/NEU posts, with the source threads listed."
    )
    question = gr.Textbox(label="Your question", placeholder="e.g. What is Melvin Hall like as a dorm?")
    ask_btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    ask_btn.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
