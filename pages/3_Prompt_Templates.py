import streamlit as st
from pathlib import Path
import datetime
import re

# Directory for saved prompts
PROMPT_DIR = Path("/app/data/saved_prompts")
PROMPT_DIR.mkdir(exist_ok=True)

# --- Default Templates ---
DEFAULT_TEMPLATES = [
    {
        "name": "Generate a Lesson Plan for New Officers",
        "text": "Generate a comprehensive lesson plan tailored for new officers.\n"
                "Imagine you've just joined the team: what critical duties, protocols, and skills do you need to master?\n"
                "What operational challenges might you face on day one?\n"
                "List the specific questions you'd ask your trainer or supervisor (e.g., about standard operating procedures, escalation pathways, stakeholder engagement, or emergency response) to ensure you're fully prepared.\n"
                "Then outline the sequence of modules, learning objectives, practical exercises, and reflection prompts that address those questions."
    },
    {
        "name": "Generate a Lesson Plan for Licensing Criteria",
        "text": "Generate a lesson plan for new officers on the key licensing criteria under the relevant regulations.\n"
                "Imagine you're a newcomer seeking to understand documentation requirements, fit-and-proper assessments, and approval workflows.\n"
                "What questions would you ask your mentor about each step?\n"
                "Then structure a session with clear learning objectives, module titles, hands-on activities, and quiz prompts to reinforce those questions."
    },
    {
        "name": "Generate a Lesson Plan for On-site Compliance Audits",
        "text": "Generate a lesson plan for new officers on conducting on-site compliance audits at licensed venues.\n"
                "Put yourself in the shoes of a fresh recruit: what checklists, risk indicators, and escalation protocols do you need clarified?\n"
                "List the questions you'd pose to the audit lead, then design modules, exercises (e.g., mock inspections), and reflection prompts to turn those questions into learning outcomes."
    },
    {
        "name": "Generate a Lesson Plan for Responsible Gambling Measures",
        "text": "Generate a lesson plan for new officers on responsible-gambling requirements.\n"
                "Imagine you're asking: which self-exclusion tools, deposit-limit controls, and reporting metrics must operators provide?\n"
                "What clarifications would you seek from the policy team?\n"
                "Then outline learning objectives, demo activities, and knowledge checks that ensure mastery of each measure."
    },
    {
        "name": "Generate a Lesson Plan for Enforcement Escalation",
        "text": "Generate a lesson plan for new officers on enforcement-escalation pathways under the relevant laws.\n"
                "Think like a new recruit: what triggers, reporting flows, and penalty scales do you need unpacked?\n"
                "Formulate the key questions you'd ask your supervisor, then map out modules, role-play scenarios, and quiz questions that address those queries step by step."
    },
    {
        "name": "Compare the regulatory reports for the periods 2017–2018 and 2021–2022",
        "text": "Compare the regulatory reports for the periods 2017–2018 and 2021–2022.\n"
                "Highlight key differences in findings, metrics, and outcomes.\n"
                "What were the major changes in regulatory focus, compliance metrics, or operational challenges between these two periods?\n"
                "Identify the most significant shifts in the regulatory approach to casino regulation and enforcement, and discuss the implications for future regulatory practices."    
    },
    {
        "name": "What are the key differences observed between Pulse Survey of 2022, 2023 and 2024",
        "text": "what are the key differences observed between Pulse Survey of 2022, 2023 and 2024"
    },
]

# Filename sanitization
def clean_filename(name: str) -> str:
    name = name.strip()
    stem = Path(name).stem
    stem = re.sub(r"[^\w\- ]+", "_", stem).strip()
    if not stem:
        stem = "untitled"
    return f"{stem}.txt"

# Save default templates to disk if they don't exist
for tpl in DEFAULT_TEMPLATES:
    fname = clean_filename(tpl["name"])
    file_path = PROMPT_DIR / fname
    if not file_path.exists():
        file_path.write_text(tpl["text"])

# Load existing prompts from disk
def load_saved_prompts():
    prompts = []
    for path in sorted(PROMPT_DIR.glob("*.txt")):
        prompts.append({"name": path.name, "text": path.read_text()})
    return prompts

# Initialize session state variables
if "saved_prompts" not in st.session_state:
    st.session_state["saved_prompts"] = load_saved_prompts()
if "editing_idx" not in st.session_state:
    st.session_state["editing_idx"] = None

# App layout
st.set_page_config(page_title="Prompt Preview", layout="wide", page_icon="📝")
st.title("Prompt Preview")

st.markdown("---")

# Help section
with st.expander("How to Use Prompt Template", expanded=False):
    st.markdown("""
    ### Prompt Template Usage Guide:
    1. **Write Your Prompt**: Use the text area to draft your prompt. This can be a question, instruction, or any text you want to use as a template.
    2. **Save Your Prompt**: Click the "Save" button to store your prompt. It will be saved in the `saved_prompts` directory.
    3. **Edit or Delete Prompts**: You can edit existing prompts by clicking the "Edit" button next
       to each saved prompt.
       To delete a prompt, click the "Delete" button.
    4. **Use Saved Prompts**: Once saved, your prompts will be listed below the input area. You can click on any prompt to view its content, edit it, or delete it.
    5. **Default Templates**: The app comes with a set of default templates that you can use as a starting point. These templates are automatically saved in the `saved_prompts` directory.
    ### Tips:
    - Use clear and concise language in your prompts to ensure they are effective.
    - Regularly review and update your saved prompts to keep them relevant.
    - You can create prompts for various purposes, such as generating lesson plans, compliance checklists, or operational guidelines.
    ### Example Prompts:
    - "Generate a comprehensive lesson plan for new officers."
    - "What are the key licensing criteria under the relevant regulations?"
    - "Outline the steps for conducting on-site compliance audits at licensed venues."
    - "What responsible gambling measures must operators provide?"
    """)



# --- form to add a new prompt ------------------------------------------
with st.form("prompt_form", clear_on_submit=True):
    prompt_text = st.text_area(
        "Write your new prompt:", height=300, key="main_prompt"
    )
    save_btn = st.form_submit_button("💾 Save", use_container_width=True)

if save_btn and prompt_text.strip():
    # Save to disk
    fname = f"prompt_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
    file_path = PROMPT_DIR / fname
    file_path.write_text(prompt_text)
    # Update session state
    st.session_state["saved_prompts"].append({"name": fname, "text": prompt_text})
    st.success(f"Prompt saved to {file_path}")
    st.rerun()

st.divider()

# --- display saved prompts ---------------------------------------------
if st.session_state["saved_prompts"]:
    st.subheader("🗂️ Saved Prompts")

    for idx, item in enumerate(st.session_state["saved_prompts"]):
        display_name = Path(item["name"]).stem
        is_editing = (st.session_state["editing_idx"] == idx)
        with st.expander(f"{idx+1}. {display_name}", expanded=is_editing):
            # EDIT MODE
            if st.session_state["editing_idx"] == idx:
                new_name = st.text_input(
                    "Name", value=Path(item["name"]).stem, key=f"name_{idx}"
                )
                edited_text = st.text_area(
                    "Prompt", value=item["text"], height=200, key=f"text_{idx}"
                )

                col_upd, col_spacer, col_cancel = st.columns([1,5,1])
                if col_upd.button("💾 Update", key=f"update_{idx}"):
                    new_name_clean = clean_filename(new_name)
                    old_path = PROMPT_DIR / item["name"]
                    new_path = PROMPT_DIR / new_name_clean

                    # Rename if needed
                    if new_name_clean != item["name"]:
                        if new_path.exists():
                            st.error("A file with that name already exists.")
                            st.stop()
                        try:
                            old_path.rename(new_path)
                        except FileNotFoundError:
                            # if the old file was a default template, it might not exist yet
                            pass
                        st.session_state["saved_prompts"][idx]["name"] = new_name_clean

                    # Update content
                    new_path.write_text(edited_text)
                    st.session_state["saved_prompts"][idx]["text"] = edited_text

                    # Exit edit mode
                    st.session_state["editing_idx"] = None
                    st.success("Saved ✅")
                    st.rerun()

                if col_cancel.button("✖ Cancel", key=f"cancel_{idx}"):
                    st.session_state["editing_idx"] = None
                    st.rerun()

            # READ-ONLY MODE
            else:
                # st.write(f"**Filename:** {item['name']}")
                st.write("**Prompt:**")
                st.code(item["text"], language="")

                col_edit, col_del = st.columns([1,1])
                if col_edit.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state["editing_idx"] = idx
                    st.rerun()

                if col_del.button("🗑️ Delete", key=f"delete_{idx}"):
                    try:
                        (PROMPT_DIR / item["name"]).unlink()
                    except FileNotFoundError:
                        pass
                    st.session_state["saved_prompts"].pop(idx)
                    st.rerun()