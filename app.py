import streamlit as st
import random

# Quiz data: image number -> hotel name
ANSWERS = {
    1: "Wynn",
    2: "Park MGM",
    3: "Mandalay Bay",
    4: "Venetian",
    5: "Mirage",
    6: "Paris",
    7: "Treasure Island",
    8: "Caesar's Palace",
    9: "Cosmopolitan",
    10: "Resorts World",
    11: "Excalibur",
    12: "The Linq",
    13: "Bellagio",
    14: "Luxor",
    15: "Planet Hollywood",
    16: "New York",
    17: "Circus Circus",
    18: "Aria",
    19: "Harrah's",
    20: "MGM Grand",
}

ALL_HOTELS = list(ANSWERS.values())


def init_session_state():
    """Initialize session state variables."""
    if "current_question" not in st.session_state:
        st.session_state.current_question = 1
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "last_correct" not in st.session_state:
        st.session_state.last_correct = None
    if "quiz_complete" not in st.session_state:
        st.session_state.quiz_complete = False
    if "mode" not in st.session_state:
        st.session_state.mode = None
    if "mc_options" not in st.session_state:
        st.session_state.mc_options = None


def get_mc_options(correct_answer):
    """Generate 4 multiple choice options including the correct answer."""
    wrong_answers = [h for h in ALL_HOTELS if h != correct_answer]
    options = random.sample(wrong_answers, 3) + [correct_answer]
    random.shuffle(options)
    return options


def check_answer(user_answer, correct_answer):
    """Check if the user's answer is correct (case-insensitive)."""
    return user_answer.strip().lower() == correct_answer.lower()


def next_question():
    """Move to the next question."""
    if st.session_state.current_question < 20:
        st.session_state.current_question += 1
        st.session_state.answered = False
        st.session_state.last_correct = None
        st.session_state.mc_options = None
    else:
        st.session_state.quiz_complete = True


def restart_quiz():
    """Reset the quiz to the beginning."""
    st.session_state.current_question = 1
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.last_correct = None
    st.session_state.quiz_complete = False
    st.session_state.mc_options = None


def main():
    st.set_page_config(
        page_title="Vegas Carpet Quiz",
        page_icon="🎰",
        layout="centered",
    )

    st.title("🎰 Vegas Carpet Quiz")
    st.markdown("*Can you identify the Las Vegas hotel by its carpet?*")

    init_session_state()

    # Mode selection
    if st.session_state.mode is None:
        st.markdown("---")
        st.subheader("Choose Your Quiz Mode")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Multiple Choice", use_container_width=True):
                st.session_state.mode = "mc"
                st.rerun()
        with col2:
            if st.button("⌨️ Type Answer", use_container_width=True):
                st.session_state.mode = "text"
                st.rerun()
        st.info("Multiple Choice: Pick from 4 options\n\nType Answer: Enter the hotel name yourself")
        return

    # Quiz complete screen
    if st.session_state.quiz_complete:
        st.markdown("---")
        st.subheader("Quiz Complete!")
        st.metric("Final Score", f"{st.session_state.score} / 20")

        percentage = (st.session_state.score / 20) * 100
        if percentage == 100:
            st.balloons()
            st.success("Perfect score! You're a Vegas carpet expert!")
        elif percentage >= 80:
            st.success("Great job! You really know your Vegas carpets!")
        elif percentage >= 60:
            st.info("Not bad! Keep practicing!")
        else:
            st.warning("Time to visit more Vegas casinos!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Play Again", use_container_width=True):
                restart_quiz()
                st.rerun()
        with col2:
            if st.button("🔀 Switch Mode", use_container_width=True):
                restart_quiz()
                st.session_state.mode = None
                st.rerun()
        return

    # Display score and progress
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Score", f"{st.session_state.score} / 20")
    with col2:
        st.metric("Question", f"{st.session_state.current_question} / 20")

    st.progress(st.session_state.current_question / 20)

    # Display current carpet image
    current_q = st.session_state.current_question
    correct_answer = ANSWERS[current_q]

    st.image(
        f"images/{current_q}.jpeg",
        caption=f"Carpet #{current_q}",
        use_container_width=True,
    )

    # Answer input based on mode
    if not st.session_state.answered:
        if st.session_state.mode == "mc":
            # Multiple choice mode
            if st.session_state.mc_options is None:
                st.session_state.mc_options = get_mc_options(correct_answer)

            st.markdown("**Which hotel has this carpet?**")
            for option in st.session_state.mc_options:
                if st.button(option, key=f"mc_{option}", use_container_width=True):
                    is_correct = option == correct_answer
                    st.session_state.answered = True
                    st.session_state.last_correct = is_correct
                    if is_correct:
                        st.session_state.score += 1
                    st.rerun()
        else:
            # Text input mode
            st.markdown("**Type the hotel name:**")
            with st.form("answer_form"):
                user_answer = st.text_input("Hotel name", label_visibility="collapsed")
                submitted = st.form_submit_button("Submit", use_container_width=True)
                if submitted and user_answer:
                    is_correct = check_answer(user_answer, correct_answer)
                    st.session_state.answered = True
                    st.session_state.last_correct = is_correct
                    if is_correct:
                        st.session_state.score += 1
                    st.rerun()
    else:
        # Show feedback
        if st.session_state.last_correct:
            st.success(f"✅ Correct! It's {correct_answer}!")
        else:
            st.error(f"❌ Wrong! The correct answer is **{correct_answer}**")

        if st.button("Next Question ➡️", use_container_width=True):
            next_question()
            st.rerun()

    # Sidebar with controls
    with st.sidebar:
        st.markdown("### Controls")
        mode_label = "Multiple Choice" if st.session_state.mode == "mc" else "Type Answer"
        st.text(f"Mode: {mode_label}")

        if st.button("🔀 Switch Mode"):
            restart_quiz()
            st.session_state.mode = None
            st.rerun()

        if st.button("🔄 Restart Quiz"):
            restart_quiz()
            st.rerun()

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "Test your knowledge of iconic Las Vegas casino carpets! "
            "Each carpet belongs to a famous Strip hotel."
        )


if __name__ == "__main__":
    main()
