import asyncio
from graph import graph
from states import State


# ============================================================
# INTERRUPT HANDLERS
# ============================================================

async def handle_roadmap_interrupt(data: dict, config: dict) -> None:
    """Prompt the user to review / edit the generated roadmap."""

    print("\n" + "=" * 60)
    print("ROADMAP REVIEW")
    print("=" * 60)
    for i, task in enumerate(data["roadmap"]):
        print(f"  {i}. {task}")
    print("\nOptions: add | delete | edit | confirm")

    while True:
        action = input("\nChoose action: ").strip().lower()

        if action == "add":
            user_action = {"action": "add", "task": input("New task title: ").strip()}
            break
        elif action == "delete":
            user_action = {"action": "delete", "index": int(input("Index to delete: ").strip())}
            break
        elif action == "edit":
            idx = int(input("Index to edit: ").strip())
            user_action = {"action": "edit", "index": idx,
                           "task": input("New title: ").strip()}
            break
        elif action == "confirm":
            user_action = {"action": "confirm"}
            break
        else:
            print("Invalid option — choose: add | delete | edit | confirm")

    await graph.aupdate_state(config, {"user_action": user_action}, as_node="review")


async def handle_quiz_permission_interrupt(data: dict, config: dict) -> None:
    """
    Ask the learner whether they want a quiz after this lesson.
    Injects quiz_permission (bool) and resumes from ask_quiz_permission
    so quiz_permission_router fires correctly.
    """
    print("\n" + "=" * 60)
    print(data.get("message", "Would you like to take a quiz? (yes / no)"))
    print("=" * 60)

    while True:
        answer = input("> ").strip().lower()
        if answer in ("yes", "y", "1"):
            permission = True
            break
        elif answer in ("no", "n", "0"):
            permission = False
            break
        else:
            print("Please type  yes  or  no.")

    await graph.aupdate_state(
        config,
        {"quiz_permission": permission},
        as_node="ask_quiz_permission",
    )


async def handle_quiz_answer_interrupt(data: dict, config: dict) -> None:
    """
    Display quiz questions and collect the student's answers.
    Injects user_answers back into state.
    """
    questions: list[str] = data["questions"]

    print("\n" + "=" * 60)
    print(data.get("quiz_text", "Quiz"))
    print("=" * 60)
    print("Answer each question below.\n")

    answers: list[str] = []
    for i, question in enumerate(questions, 1):
        print(f"Q{i}: {question}")
        answers.append(input("Your answer: ").strip())
        print()

    await graph.aupdate_state(
        config,
        {"user_answers": answers},
        as_node="quiz_hitl",
    )


async def handle_challenge_interrupt(data: dict, config: dict) -> None:
    """
    Show the 'Ready for a challenge?' prompt and record the user's choice.
    Injects challenge_accepted (bool) and resumes from ask_challenge so
    challenge_router fires correctly.
    """
    print("\n" + "=" * 60)
    print(data.get("message", "🏆  Ready for a challenge? (yes / no)"))
    print("=" * 60)

    while True:
        answer = input("> ").strip().lower()
        if answer in ("yes", "y", "1"):
            accepted = True
            break
        elif answer in ("no", "n", "0"):
            accepted = False
            print("\n⏭️  No problem — moving on to the next lesson.")
            break
        else:
            print("Please type  yes  or  no.")

    await graph.aupdate_state(
        config,
        {"challenge_accepted": accepted},
        as_node="ask_challenge",
    )


async def handle_interrupt(data: dict, config: dict) -> None:
    """Dispatch to the correct handler based on interrupt type."""
    interrupt_type = data.get("type", "")

    if interrupt_type == "roadmap_review":
        await handle_roadmap_interrupt(data, config)
    elif interrupt_type == "quiz_permission":
        await handle_quiz_permission_interrupt(data, config)
    elif interrupt_type == "quiz_answer":
        await handle_quiz_answer_interrupt(data, config)
    elif interrupt_type == "challenge_prompt":
        await handle_challenge_interrupt(data, config)
    else:
        print(f"[test] Unknown interrupt type: '{interrupt_type}'")
        print(f"[test] Raw data: {data}")


# ============================================================
# STREAMING HELPER
# ============================================================

async def stream_until_interrupt_or_end(stream_input, config: dict) -> bool:
    """
    Stream graph events.
    Returns True  — interrupt hit (caller must re-stream to continue).
    Returns False — graph ran to completion.
    """
    async for event in graph.astream(stream_input, config=config):

        for node, output in event.items():

            # ── LangGraph interrupt signal ─────────────────────────
            if node == "__interrupt__":
                await handle_interrupt(output[0].value, config)
                return True

            # ── Normal node output ─────────────────────────────────
            print(f"\n{'─' * 55}")
            print(f"▶ Node: {node}")

            if not isinstance(output, dict):
                continue

            if "lesson" in output and output["lesson"]:
                print("\n📖  Lesson:\n")
                print(output["lesson"])

            if "evaluation_result" in output and output["evaluation_result"]:
                print("\n✅  Quiz Evaluation:\n")
                print(output["evaluation_result"])

            # project text is already printed inside project_node itself,
            # so we don't double-print here — just acknowledge the node ran.

    return False


# ============================================================
# MAIN
# ============================================================

async def main() -> None:

    topic = input("Enter topic to learn: ").strip()
    config = {"configurable": {"thread_id": "gyanpath-session-1"}}

    print(f"\n🚀  Starting GyanPath for: '{topic}'\n")

    # First call — pass the initial State object
    interrupted = await stream_until_interrupt_or_end(State(topic=topic), config)

    # Resume loop — pass None so LangGraph continues from its checkpoint
    while interrupted:
        interrupted = await stream_until_interrupt_or_end(None, config)

    result = await graph.aget_state(config)
    if result.values.get("finished"):
        print("\n🎓  Learning complete. Well done!")
    else:
        print("\nGraph ended.")


if __name__ == "__main__":
    asyncio.run(main())
