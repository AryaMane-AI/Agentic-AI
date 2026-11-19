"""Interactive runner for Labs 1-14.

Run from the project root:
    python DEMO_ALL_14_LABS.py
    python DEMO_ALL_14_LABS.py --lab 8
    python DEMO_ALL_14_LABS.py --lab 10 --input "ERROR database timeout"

No canned scenarios are executed. The user chooses a lab and supplies every
prompt/input at runtime. JSON input is accepted for labs with structured actions.
"""
from __future__ import annotations
import argparse, json, sys, textwrap
from agentic_core.runtime import run_lab

LABS = {
 1: ("Agent vs Chatbot", "Enter a natural-language request. The agent chooses a tool; the chatbot side remains text-only."),
 2: ("Tool-Using Agent", "Use: calculate <expression> | find course <course name> | analyse <your text> | list tools."),
 3: ("Reusable Skills", 'Enter JSON: {"action":"create","name":"my_skill","description":"...","operation":"uppercase"}; then run with {"action":"run","name":"my_skill","input":"your text"}. Operations: uppercase, lowercase, word_count, character_count, extract_emails, calculate, course_lookup.'),
 4: ("Memory & Retrieval", 'Enter JSON: {"action":"remember","user_id":"student1","text":"your memory"} or {"action":"recall","user_id":"student1","query":"search words"}.'),
 5: ("Connectors", 'Enter JSON: {"action":"list"}, or {"action":"call","connector":"academic_db","arguments":{"query":"your course"}}. workspace_files supports list/read/write.'),
 6: ("Agent Runtime", "Enter a task in natural language. Runtime records status, duration, run ID and execution events."),
 7: ("Agentic Node Graph", 'Enter JSON: {"nodes":[{"id":"n1","operation":"word_count","input":"your text"},{"id":"n2","operation":"uppercase","input":"your text","depends_on":["n1"]}]}. Operations depend on the graph implementation.'),
 8: ("Parallel Agent Swarm", "Enter any text for parallel entity, keyword, sentiment and statistics analysis."),
 9: ("Deep Research", 'Enter a topic, or JSON: {"topic":"your topic","sources":[{"title":"Your source title","text":"Evidence text supplied by you"}]}. Local evidence corpus; not live web search.'),
 10: ("Cloud Operations", 'Enter raw log lines, or JSON: {"service":"your-service","environment":"test","logs":"INFO started\\nERROR timeout\\nWARNING high memory"}.'),
 11: ("Agentic SDLC Factory", "Enter a software requirement in your own words; the lab generates planning, acceptance and test artifacts."),
 12: ("Safety & Governance", 'Enter a governance proposal as JSON with fields such as diagnosis, proposed_change, rollback_plan, privacy_scrubbed, estimated_cost and budget.'),
 13: ("Engineering Specialist", 'Enter JSON with domain and readings, e.g. {"domain":"mechanical","readings":[{"temperature_c":75,"vibration_mm_s":4}]}. Use the supported domain-specific reading keys.'),
 14: ("Capstone Project Studio", 'Enter JSON: {"action":"triage","user_id":"student1","issue":"describe your issue"}; actions include create, list, get, update, close and triage.'),
}

def show_labs():
    print("\nAVAILABLE LABS")
    for n,(title,desc) in LABS.items():
        print(f"{n:>2}. Lab {n}: {title}")

def run_one(lab:int, supplied:str|None=None):
    title, help_text = LABS[lab]
    print(f"\n{'='*76}\nLAB {lab}: {title}\n{'='*76}")
    print(textwrap.fill(help_text, width=90))
    prompt = supplied if supplied is not None else input("\nEnter your own input (or type :back to choose another lab):\n> ").strip()
    if prompt == ":back": return True
    if not prompt:
        print("Input cannot be empty. No execution was recorded.")
        return False
    result=run_lab(lab,prompt)
    print("\nACTUAL USER INPUT:\n", prompt)
    print("\nRESULT:\n", json.dumps(result.get("output"), indent=2, ensure_ascii=False, default=str))
    print(f"\nSTATUS: {result.get('status')} | RUN ID: {result.get('run_id')} | DURATION: {result.get('duration_seconds')}s")
    print("Execution record saved in course_organizer/database/agentic_core.sqlite3")
    return result.get("success",False)

def main():
    parser=argparse.ArgumentParser(description="Choose any lab and provide your own input")
    parser.add_argument("--lab",type=int,choices=range(1,15),help="Run one selected lab")
    parser.add_argument("--input",type=str,help="Provide input directly (requires --lab)")
    args=parser.parse_args()
    if args.input is not None and args.lab is None:
        parser.error("--input requires --lab")
    if args.lab:
        ok=run_one(args.lab,args.input)
        return 0 if ok else 1
    print("\nAGENTIC AI COURSE ORGANIZER — INTERACTIVE 14-LAB RUNNER")
    print("Choose a lab and type your own prompt/input. No predefined demo scenario is run.")
    while True:
        show_labs()
        choice=input("\nChoose lab number 1-14, or 0 to exit: ").strip()
        if choice=="0":
            print("Demo ended. Your execution history remains saved.")
            break
        if not choice.isdigit() or int(choice) not in LABS:
            print("Please enter a number from 1 to 14, or 0 to exit.")
            continue
        run_one(int(choice))
        again=input("\nRun another lab? [Y/n]: ").strip().lower()
        if again in {"n","no"}:
            break
    return 0

if __name__=="__main__":
    sys.exit(main())
