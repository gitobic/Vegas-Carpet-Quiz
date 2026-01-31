# Vegas Carpet Quiz

Can you identify the Las Vegas location by its carpet? Test your knowledge of iconic casino floor patterns from the Las Vegas Strip and beyond. 

**[Play the Quiz](https://vegas-carpet-quiz.streamlit.app/)**

# Why  
I have had this idea rolling around for a while, but never did anything about. Finally, with Claude, it was a great opportunity to go through the whole process *again* and apply all my learnings.  Also, I wanted to test out an idea with Streamlit.  The global leaderboard - how do you store data without a database and associated infra? I hit on the idea of using a GitHub Gist that the Streamlit app could update and read from.  Will it scale? No. But does it work for the handful of visitors? Quite well...  So.. Good Luck!

## Features

- **556 Carpet Images**: From Aria to Wynn, covering casinos, hotels, lounges, and more
- **Configurable Quiz Length**: Choose 10, 20, or 50 questions
- **Two Difficulty Levels**:
  - **Easy**: Identify the facility (4 multiple choice options)
  - **Hard**: Two-step challenge - first identify the facility, then the area type (casino, hotel, amenity, etc.). Must get both correct to score!
- **Personal High Scores**: Track your best scores per difficulty and quiz length
- **Global Leaderboard**: Compete against other players (top 10 per category)
- **Player Taglines**: Fun titles like "Casual Vacationer" or "Carpet Nerd" based on your quiz settings
- **Instant Feedback**: Learn about each carpet after answering

## Run Locally

```bash
uv run streamlit run app.py
```

Or with pip:
```bash
pip install streamlit
streamlit run app.py
```

## Facilities Featured

70+ Las Vegas properties including: Aria, Bellagio, Caesars Palace, Cosmopolitan, Encore, Fontainebleau, Luxor, Mandalay Bay, MGM Grand, Mirage, Paris, Resorts World, Venetian, Wynn, and many more.

## Area Types

Carpets are categorized into 8 area types:
- Amenity
- Buffet
- Casino
- Convention
- Hotel
- Lounge
- Restaurant
- Retail

## Credits

- **Carpet Photography**: [Brent Maynard](https://www.brentmaynard.com/casino-carpet.html)
- **App Development**: T. Gossen and Claude (Anthropic)

## License

MIT License - See [LICENSE](LICENSE) for details.
