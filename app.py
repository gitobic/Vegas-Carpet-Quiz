import streamlit as st
import streamlit_shadcn_ui as ui
import random
import requests
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Known types for reliable filename parsing
KNOWN_TYPES = frozenset([
    'amenity', 'buffet', 'casino', 'convention',
    'hotel', 'lounge', 'restaurant', 'retail'
])

# Display names for types
TYPE_DISPLAY = {
    'amenity': 'Amenity',
    'buffet': 'Buffet',
    'casino': 'Casino',
    'convention': 'Convention',
    'hotel': 'Hotel',
    'lounge': 'Lounge',
    'restaurant': 'Restaurant',
    'retail': 'Retail'
}

# Taglines based on quiz configuration
TAGLINES = {
    (10, 'easy'): "Casual Vacationer",
    (10, 'hard'): "Annual Convention Attendee",
    (20, 'easy'): "Strip Regular",
    (20, 'hard'): "Frequent Flyer",
    (50, 'easy'): "Vegas Veteran",
    (50, 'hard'): "Carpet Nerd",
}

MAX_LEADERBOARD_ENTRIES = 10


@dataclass
class CarpetImage:
    """Represents a carpet image with its metadata."""
    filename: str
    facility: str
    type: str
    space: str
    description: str

    @property
    def image_path(self) -> str:
        return f"carpets/{self.filename}"

    @property
    def display_facility(self) -> str:
        """Convert facility slug to display name."""
        return self.facility.replace('-', ' ').title()

    @property
    def display_type(self) -> str:
        return TYPE_DISPLAY.get(self.type, self.type.title())


def parse_carpet_filename(filename: str) -> tuple:
    """Parse carpet filename to extract facility, type, and space."""
    base = filename.rsplit('.', 1)[0]
    parts = base.split('-')

    type_index = None
    for i, part in enumerate(parts):
        if part in KNOWN_TYPES:
            type_index = i
            break

    if type_index is None:
        raise ValueError(f"No known type found in filename: {filename}")

    facility = '-'.join(parts[:type_index])
    carpet_type = parts[type_index]
    space = '-'.join(parts[type_index + 1:])

    return facility, carpet_type, space


@st.cache_data
def load_carpet_data(carpets_dir: str = "carpets") -> List[CarpetImage]:
    """Load all carpet images and their descriptions."""
    carpets = []
    carpet_path = Path(carpets_dir)

    for jpg_file in sorted(carpet_path.glob("*.jpg")):
        txt_file = jpg_file.with_suffix('.txt')

        description = ""
        if txt_file.exists():
            description = txt_file.read_text().strip()

        try:
            facility, carpet_type, space = parse_carpet_filename(jpg_file.name)
        except ValueError:
            continue

        carpets.append(CarpetImage(
            filename=jpg_file.name,
            facility=facility,
            type=carpet_type,
            space=space,
            description=description
        ))

    return carpets


# --- Gist-based Leaderboard Functions ---

def get_gist_config() -> Optional[dict]:
    """Get Gist configuration from Streamlit secrets."""
    try:
        return {
            'token': st.secrets['gist']['token'],
            'gist_id': st.secrets['gist']['gist_id'],
            'filename': st.secrets['gist'].get('filename', 'scores.json')
        }
    except (KeyError, FileNotFoundError):
        return None


@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_leaderboard() -> dict:
    """Fetch leaderboard from GitHub Gist."""
    config = get_gist_config()
    if not config:
        return {}

    try:
        response = requests.get(
            f"https://api.github.com/gists/{config['gist_id']}",
            headers={'Authorization': f"token {config['token']}"},
            timeout=5
        )
        if response.status_code == 200:
            gist_data = response.json()
            content = gist_data['files'][config['filename']]['content']
            return json.loads(content)
    except Exception:
        pass
    return {}


def save_score_to_leaderboard(name: str, score: int, difficulty: str, question_count: int) -> bool:
    """Save a score to the GitHub Gist leaderboard."""
    config = get_gist_config()
    if not config:
        return False

    # Clear cache to get fresh data
    fetch_leaderboard.clear()

    try:
        # Fetch current leaderboard
        response = requests.get(
            f"https://api.github.com/gists/{config['gist_id']}",
            headers={'Authorization': f"token {config['token']}"},
            timeout=5
        )
        if response.status_code != 200:
            return False

        gist_data = response.json()
        content = gist_data['files'][config['filename']]['content']
        leaderboard = json.loads(content)

        # Create category key
        category = f"{difficulty}_{question_count}"
        if category not in leaderboard:
            leaderboard[category] = []

        # Add new score
        leaderboard[category].append({
            'name': name[:20],  # Limit name length
            'score': score,
            'date': datetime.now().strftime('%Y-%m-%d')
        })

        # Sort by score (descending) and keep top entries
        leaderboard[category] = sorted(
            leaderboard[category],
            key=lambda x: (-x['score'], x['date'])
        )[:MAX_LEADERBOARD_ENTRIES]

        # Update gist
        update_response = requests.patch(
            f"https://api.github.com/gists/{config['gist_id']}",
            headers={
                'Authorization': f"token {config['token']}",
                'Content-Type': 'application/json'
            },
            json={
                'files': {
                    config['filename']: {
                        'content': json.dumps(leaderboard, indent=2)
                    }
                }
            },
            timeout=5
        )
        return update_response.status_code == 200
    except Exception:
        return False


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'config': None,
        'quiz_questions': [],
        'current_index': 0,
        'score': 0,
        'answered': False,
        'last_correct': None,
        'mc_options': None,
        'high_scores': {},
        'hard_step': 'facility',
        'facility_correct': None,
        'selected_facility': None,
        'score_submitted': False,
        'player_name': '',
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_quiz(question_count: int, difficulty: str):
    """Initialize a new quiz with random questions."""
    all_carpets = load_carpet_data()

    selected = random.sample(all_carpets, min(question_count, len(all_carpets)))

    st.session_state.config = {'question_count': question_count, 'difficulty': difficulty}
    st.session_state.quiz_questions = selected
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.last_correct = None
    st.session_state.mc_options = None
    st.session_state.hard_step = 'facility'
    st.session_state.facility_correct = None
    st.session_state.selected_facility = None
    st.session_state.score_submitted = False


def get_facility_options(current_carpet: CarpetImage, all_carpets: List[CarpetImage]) -> List[str]:
    """Generate 4 facility options including the correct answer."""
    correct = current_carpet.display_facility
    all_facilities = list(set(
        c.display_facility for c in all_carpets
        if c.facility != current_carpet.facility
    ))
    wrong_answers = random.sample(all_facilities, min(3, len(all_facilities)))
    options = wrong_answers[:3] + [correct]
    random.shuffle(options)
    return options


def get_type_options() -> List[str]:
    """Return all 8 type options."""
    return list(TYPE_DISPLAY.values())


def next_question():
    """Move to the next question."""
    st.session_state.current_index += 1
    st.session_state.answered = False
    st.session_state.last_correct = None
    st.session_state.mc_options = None
    st.session_state.hard_step = 'facility'
    st.session_state.facility_correct = None
    st.session_state.selected_facility = None


def complete_quiz():
    """Handle quiz completion and high score tracking."""
    config = st.session_state.config
    score = st.session_state.score
    score_key = (config['difficulty'], config['question_count'])

    if score_key not in st.session_state.high_scores:
        st.session_state.high_scores[score_key] = score
    else:
        st.session_state.high_scores[score_key] = max(
            st.session_state.high_scores[score_key], score
        )


def get_estimated_time(question_count: int) -> str:
    """Estimate quiz completion time."""
    minutes = question_count // 4  # ~15 seconds per question
    if minutes < 1:
        return "~1 min"
    return f"~{minutes} min"


def get_average_score(leaderboard: dict, difficulty: str, question_count: int) -> float:
    """Calculate average score from leaderboard for a category."""
    category = f"{difficulty}_{question_count}"
    if category not in leaderboard or not leaderboard[category]:
        return 0
    scores = [entry['score'] for entry in leaderboard[category]]
    return sum(scores) / len(scores)


def show_landing_page():
    """Display the landing page with quiz configuration options."""
    st.markdown("# 🎰 Vegas Carpet Quiz")
    st.markdown("*Can you identify the Las Vegas location by its carpet?*")

    # Subtle stats (reduced visual weight)
    st.caption("556 carpets • 70+ Vegas properties • No repeats per quiz")

    st.markdown("")

    # === STEP 1: Quiz Length ===
    st.markdown("##### How long do you want to play?")
    question_count = st.radio(
        "Quiz length",
        options=[10, 20, 50],
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("")

    # === STEP 2: Difficulty ===
    st.markdown("##### Choose your challenge")
    col1, col2 = st.columns(2)
    with col1:
        easy_selected = st.button(
            "🎯 Easy",
            key="easy_btn",
            width="stretch",
            type="secondary"
        )
        st.caption("Popular carpets • Guess the facility")
    with col2:
        hard_selected = st.button(
            "🔥 Hard",
            key="hard_btn",
            width="stretch",
            type="secondary"
        )
        st.caption("Deep cuts • Facility + area type")

    # Track difficulty selection in session state
    if 'selected_difficulty' not in st.session_state:
        st.session_state.selected_difficulty = 'easy'
    if easy_selected:
        st.session_state.selected_difficulty = 'easy'
    if hard_selected:
        st.session_state.selected_difficulty = 'hard'

    difficulty = st.session_state.selected_difficulty

    # Show current selection with tagline
    diff_display = "Easy" if difficulty == "easy" else "Hard"
    tagline = TAGLINES.get((question_count, difficulty), "")
    st.markdown(f"**Selected:** {diff_display} mode")
    if tagline:
        st.markdown(f"*\"{tagline}\"*")

    st.markdown("")

    # === PRIMARY CTA: Start Quiz ===
    estimated_time = get_estimated_time(question_count)
    diff_desc = "Guess the facility" if difficulty == "easy" else "Facility + area type"

    if st.button("🎰 Start Quiz", key="start_btn", type="primary", width="stretch"):
        start_quiz(question_count, difficulty)
        st.rerun()

    # Microcopy below button
    st.caption(f"{question_count} questions • {diff_display} mode • {estimated_time}")

    # Session best (if exists)
    score_key = (difficulty, question_count)
    if score_key in st.session_state.high_scores:
        best = st.session_state.high_scores[score_key]
        st.success(f"Your best: {best}/{question_count}")

    st.markdown("---")

    # === LEADERBOARD TEASER (collapsed) ===
    show_leaderboard_teaser(difficulty, question_count)


def show_leaderboard_teaser(difficulty: str, question_count: int):
    """Show a lightweight leaderboard teaser, with full board in expander."""
    if not get_gist_config():
        return

    leaderboard = fetch_leaderboard()

    # Calculate average for current selection
    avg_score = get_average_score(leaderboard, difficulty, question_count)

    if avg_score > 0:
        st.markdown("##### Can you beat the average?")
        diff_display = "Easy" if difficulty == "easy" else "Hard"
        st.markdown(f"**{diff_display} ({question_count}Q) average:** {avg_score:.1f}/{question_count}")
    else:
        st.markdown("##### Be the first on the leaderboard!")
        st.caption("No scores recorded yet for this mode.")

    # Full leaderboard in expander (collapsed by default)
    with st.expander("View Full Leaderboard"):
        show_full_leaderboard(leaderboard)


def show_full_leaderboard(leaderboard: dict):
    """Display the full global leaderboard."""
    if not leaderboard:
        st.caption("No scores yet. Be the first!")
        return

    categories = list(leaderboard.keys())
    if not categories:
        st.caption("No scores yet. Be the first!")
        return

    def format_category(cat):
        diff, count = cat.split('_')
        return f"{diff.title()} ({count}Q)"

    tabs = st.tabs([format_category(c) for c in sorted(categories)])

    for tab, category in zip(tabs, sorted(categories)):
        with tab:
            scores = leaderboard.get(category, [])
            if scores:
                for i, entry in enumerate(scores[:10], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    diff, count = category.split('_')
                    st.text(f"{medal} {entry['name']}: {entry['score']}/{count}")
            else:
                st.caption("No scores in this category yet.")


def show_quiz_question():
    """Display the current quiz question."""
    config = st.session_state.config
    questions = st.session_state.quiz_questions
    idx = st.session_state.current_index
    current = questions[idx]

    # Score and question badges
    diff_label = "Easy" if config['difficulty'] == "easy" else "Hard"
    ui.badges(
        badge_list=[
            (f"Score: {st.session_state.score}/{config['question_count']}", "default"),
            (f"Q {idx + 1}/{config['question_count']}", "secondary"),
            (diff_label, "outline")
        ],
        key=f"quiz_badges_{idx}"
    )

    st.progress((idx + 1) / config['question_count'])

    st.image(current.image_path, width="stretch")

    if config['difficulty'] == "easy":
        show_easy_mode(current)
    else:
        show_hard_mode(current)


def show_easy_mode(current: CarpetImage):
    """Easy mode: just identify the facility."""
    if st.session_state.mc_options is None:
        all_carpets = load_carpet_data()
        st.session_state.mc_options = get_facility_options(current, all_carpets)

    if not st.session_state.answered:
        st.markdown("**Which facility has this carpet?**")

        for option in st.session_state.mc_options:
            if st.button(option, key=f"mc_{option}", width="stretch"):
                is_correct = option == current.display_facility
                st.session_state.answered = True
                st.session_state.last_correct = is_correct
                if is_correct:
                    st.session_state.score += 1
                st.rerun()
    else:
        if st.session_state.last_correct:
            st.success(f"Correct! {current.display_facility}")
        else:
            st.error(f"Wrong! The correct answer is **{current.display_facility}**")

        if current.description:
            st.info(f"**About this carpet:** {current.description}")

        if st.button("Next Question", type="primary", width="stretch"):
            next_question()
            if st.session_state.current_index >= st.session_state.config['question_count']:
                complete_quiz()
            st.rerun()


def show_hard_mode(current: CarpetImage):
    """Hard mode: two-step - identify facility, then type."""

    if st.session_state.hard_step == 'facility':
        if st.session_state.mc_options is None:
            all_carpets = load_carpet_data()
            st.session_state.mc_options = get_facility_options(current, all_carpets)

        st.markdown("**Step 1: Which facility has this carpet?**")

        for option in st.session_state.mc_options:
            if st.button(option, key=f"facility_{option}", width="stretch"):
                is_correct = option == current.display_facility
                st.session_state.facility_correct = is_correct
                st.session_state.selected_facility = option
                st.session_state.hard_step = 'type'
                st.session_state.mc_options = None
                st.rerun()

    elif st.session_state.hard_step == 'type' and not st.session_state.answered:
        if st.session_state.facility_correct:
            st.success(f"Step 1: Correct! {current.display_facility}")
        else:
            st.error(f"Step 1: Wrong! It was **{current.display_facility}** (you chose {st.session_state.selected_facility})")

        st.markdown("**Step 2: What type of area is this?**")

        type_options = get_type_options()
        for option in type_options:
            if st.button(option, key=f"type_{option}", width="stretch"):
                type_correct = option == current.display_type
                both_correct = st.session_state.facility_correct and type_correct
                st.session_state.answered = True
                st.session_state.last_correct = both_correct
                if both_correct:
                    st.session_state.score += 1
                st.session_state.type_correct = type_correct
                st.session_state.selected_type = option
                st.rerun()

    else:
        if st.session_state.facility_correct:
            st.success(f"Step 1: Correct! {current.display_facility}")
        else:
            st.error(f"Step 1: Wrong! It was **{current.display_facility}**")

        type_correct = getattr(st.session_state, 'type_correct', False)
        selected_type = getattr(st.session_state, 'selected_type', '')

        if type_correct:
            st.success(f"Step 2: Correct! {current.display_type}")
        else:
            st.error(f"Step 2: Wrong! It was **{current.display_type}** (you chose {selected_type})")

        if st.session_state.last_correct:
            st.success("Both correct! +1 point")
        else:
            st.warning("Must get both correct to score.")

        if current.description:
            st.info(f"**About this carpet:** {current.description}")

        if st.button("Next Question", type="primary", width="stretch"):
            next_question()
            if st.session_state.current_index >= st.session_state.config['question_count']:
                complete_quiz()
            st.rerun()


def show_quiz_complete():
    """Display the quiz complete screen with score and high score."""
    config = st.session_state.config
    score = st.session_state.score
    total = config['question_count']
    score_key = (config['difficulty'], config['question_count'])
    best_score = st.session_state.high_scores.get(score_key, score)

    st.markdown("# 🎰 Quiz Complete!")

    col1, col2 = st.columns(2)
    with col1:
        percentage = int((score / total) * 100)
        ui.metric_card(
            title="Your Score",
            content=f"{score}/{total}",
            description=f"{percentage}% correct",
            key="score_card"
        )
    with col2:
        ui.metric_card(
            title="Session Best",
            content=f"{best_score}/{total}",
            description="personal record",
            key="best_card"
        )

    percentage = (score / total) * 100
    if percentage == 100:
        st.balloons()
        st.success("Perfect score! You're a true Vegas carpet expert!")
    elif percentage >= 80:
        st.success("Excellent! You really know your Vegas carpets!")
    elif percentage >= 60:
        st.info("Good job! Keep practicing!")
    else:
        st.warning("Time to visit more Vegas casinos!")

    if score == best_score and score > 0:
        st.success("New session best!")

    # Leaderboard submission
    if get_gist_config() and not st.session_state.score_submitted:
        st.markdown("---")
        st.subheader("Submit to Global Leaderboard")

        name = st.text_input(
            "Enter your name:",
            max_chars=20,
            placeholder="Your nickname"
        )

        if st.button("Submit Score", type="primary", disabled=not name):
            if save_score_to_leaderboard(name, score, config['difficulty'], config['question_count']):
                st.session_state.score_submitted = True
                st.success(f"Score submitted! Check the leaderboard.")
                st.rerun()
            else:
                st.error("Failed to submit score. Try again.")

    elif st.session_state.score_submitted:
        st.success("Score submitted to leaderboard!")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Play Again", width="stretch"):
            start_quiz(config['question_count'], config['difficulty'])
            st.rerun()
    with col2:
        if st.button("Change Settings", width="stretch"):
            st.session_state.config = None
            st.rerun()


def main():
    st.set_page_config(
        page_title="Vegas Carpet Quiz",
        page_icon="🎰",
        layout="centered",
    )

    init_session_state()

    if st.session_state.config is None:
        show_landing_page()
    elif st.session_state.current_index >= st.session_state.config['question_count']:
        show_quiz_complete()
    else:
        show_quiz_question()

    with st.sidebar:
        st.markdown("### 🎰 Vegas Carpet Quiz")

        # Current quiz status (if playing)
        if st.session_state.config is not None:
            config = st.session_state.config
            diff_label = "Easy" if config['difficulty'] == "easy" else "Hard"
            st.caption(f"Playing: {diff_label} • {config['question_count']}Q")

            if st.button("✕ Quit Quiz", width="stretch"):
                st.session_state.config = None
                st.rerun()
            st.markdown("---")

        # Leaderboard in sidebar (FIRST - most prominent)
        if get_gist_config():
            with st.expander("📊 Leaderboard", expanded=False):
                leaderboard = fetch_leaderboard()
                # Show all 6 permutations in logical order
                all_categories = [
                    ("easy_10", "Easy (10Q)"),
                    ("easy_20", "Easy (20Q)"),
                    ("easy_50", "Easy (50Q)"),
                    ("hard_10", "Hard (10Q)"),
                    ("hard_20", "Hard (20Q)"),
                    ("hard_50", "Hard (50Q)"),
                ]
                has_scores = False
                for cat_key, cat_label in all_categories:
                    if cat_key in leaderboard and leaderboard[cat_key]:
                        has_scores = True
                        count = cat_key.split('_')[1]
                        st.caption(cat_label)
                        for i, entry in enumerate(leaderboard[cat_key][:3], 1):
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                            st.text(f"{medal} {entry['name']}: {entry['score']}/{count}")
                if not has_scores:
                    st.caption("No scores yet!")

        # How to Play & Scoring (combined)
        with st.expander("📖 How to Play & Scoring"):
            st.markdown("""
**Easy Mode**
- Pick the correct facility from 4 options
- 1 point per correct answer

**Hard Mode**
- First: identify the facility
- Then: identify the area type
- Must get BOTH correct to score

---

**Scoring**
- 🏆 **100%** — Vegas Carpet Expert!
- ⭐ **80%+** — Excellent knowledge
- 👍 **60%+** — Good job, keep practicing
- 🎰 **<60%** — Time to visit more casinos!
            """)

        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
556 carpet photos from 70+ Las Vegas properties.

**Photo Credits**
[Brent Maynard](https://www.brentmaynard.com/casino-carpet.html)

**Source Code**
[GitHub](https://github.com/gitobic/Vegas-Carpet-Quiz)

Built with Streamlit by T. Gossen & Claude
            """)


if __name__ == "__main__":
    main()
