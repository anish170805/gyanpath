import asyncio
from graph import graph
from states import State


# ============================================================
# INTERRUPT HANDLERS
# ============================================================

async def handle_roadmap_interrupt(data: dict, config: dict):
    """Prompt the user to review / edit the roadmap."""

    roadmap = data["roadmap"]

    print("\n" + "=" * 60)
    print("ROADMAP REVIEW")
    print("=" * 60)
    for i, task in enumerate(roadmap):
        print(f"  {i}. {task}")
    print("\nOptions: add | delete | edit | confirm")

    while True:
        action = input("\nChoose action: ").strip().lower()

        if action == "add":
            task = input("Enter new task title: ").strip()
            user_action = {"action": "add", "task": task}
            break

        elif action == "delete":
            idx = int(input("Enter index to delete: ").strip())
            user_action = {"action": "delete", "index": idx}
            break

        elif action == "edit":
            idx = int(input("Enter index to edit: ").strip())
            task = input("Enter new title: ").strip()
            user_action = {"action": "edit", "index": idx, "task": task}
            break

        elif action == "confirm":
            user_action = {"action": "confirm"}
            break

        else:
            print("Invalid option. Please choose: add | delete | edit | confirm")

    # Resume from the review node so the roadmap_router fires correctly
    await graph.aupdate_state(
        config,
        {"user_action": user_action},
        as_node="review"
    )


async def handle_quiz_interrupt(data: dict, config: dict):
    """
    Display quiz questions and collect the student's answers.
    Answers are injected into state as `user_answers`.
    """
    questions: list[str] = data["questions"]

    print("\n" + "=" * 60)
    print(data.get("quiz_text", "Quiz"))
    print("=" * 60)
    print("Please answer each question below.\n")

    answers: list[str] = []
    for i, question in enumerate(questions, 1):
        print(f"Q{i}: {question}")
        answer = input("Your answer: ").strip()
        answers.append(answer)
        print()

    # Inject answers; resume from quiz_hitl so the edge to evaluate_quiz fires
    await graph.aupdate_state(
        config,
        {"user_answers": answers},
        as_node="quiz_hitl"
    )


async def handle_interrupt(data: dict, config: dict):
    """Dispatch to the correct handler based on interrupt type."""

    interrupt_type = data.get("type", "")

    if interrupt_type == "roadmap_review":
        await handle_roadmap_interrupt(data, config)

    elif interrupt_type == "quiz_answer":
        await handle_quiz_interrupt(data, config)

    else:
        print(f"[test] Unknown interrupt type: '{interrupt_type}'")
        print(f"[test] Data: {data}")


# ============================================================
# STREAMING HELPER
# ============================================================

async def stream_until_interrupt_or_end(stream_input, config: dict) -> bool:
    """
    Stream graph events.
    - Returns True  if an interrupt was hit (caller should re-stream).
    - Returns False if the graph ran to completion.
    """
    async for event in graph.astream(stream_input, config=config):

        for node, output in event.items():

            # ── INTERRUPT ──────────────────────────────────────────
            if node == "__interrupt__":
                interrupt_value = output[0].value
                await handle_interrupt(interrupt_value, config)
                return True   # paused — caller must re-stream

            # ── NORMAL NODE OUTPUT ─────────────────────────────────
            print(f"\n{'─' * 50}")
            print(f"Node executed: {node}")

            if not isinstance(output, dict):
                continue

            if "lesson" in output:
                print("\n📖  Lesson:\n")
                print(output["lesson"])

            if "quiz_text" in output and output["quiz_text"]:
                # quiz_text is shown during the interrupt, not here
                pass

            if "evaluation_result" in output and output["evaluation_result"]:
                print("\n✅  Quiz Evaluation:\n")
                print(output["evaluation_result"])

    # Fell through without hitting an interrupt → graph finished
    return False


# ============================================================
# MAIN
# ============================================================

async def main():

    topic = input("Enter topic to learn: ").strip()

    state = State(topic=topic)

    config = {
        "configurable": {
            "thread_id": "gyanpath-session-1"
        }
    }

    print(f"\n🚀 Starting GyanPath for topic: '{topic}'\n")

    # First run: pass the initial state
    interrupted = await stream_until_interrupt_or_end(state, config)

    # Resume loop: pass None so LangGraph continues from its checkpoint
    while interrupted:
        interrupted = await stream_until_interrupt_or_end(None, config)

    # Final status
    result = await graph.aget_state(config)
    if result.values.get("finished"):
        print("\n🎓  Learning complete. Well done!")
    else:
        print("\nGraph ended.")


if __name__ == "__main__":
    asyncio.run(main())
