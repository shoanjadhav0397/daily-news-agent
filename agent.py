import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import feedparser
from google import genai

# Configuration
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
]


def fetch_top_news(limit=10):
    """Collects headlines and summaries from authentic RSS feeds."""
    articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            articles.append(f"- Title: {title}\n  Context: {summary}\n  Source: {link}")
            if len(articles) >= limit:
                return "\n\n".join(articles)
    return "\n\n".join(articles[:limit])


def generate_summary(news_data):
    """Uses Gemini to synthesize the top stories into 4-5 sentences."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    You are an objective international news editor.
    Below are the top 10 raw news entries gathered today from verified wire feeds:
    
    {news_data}
    
    Task:
    Provide an executive summary of today's global landscape.
    Rules:
    1. The entire summary MUST be strictly 4 to 5 sentences long.
    2. Focus only on high-impact global geopolitical, economic, and humanitarian developments.
    3. Maintain an objective, journalistic tone.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    return response.text.strip()


def send_email(content):
    """Dispatches the digest via Gmail SMTP."""
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = "🌍 Daily Top 10 International Briefing"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #222;">
        <h2 style="color: #1a365d;">Daily World Briefing</h2>
        <p style="font-size: 15px; background: #f7fafc; border-left: 4px solid #3182ce; padding: 12px;">
          {content.replace(chr(10), '<br>')}
        </p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-top: 20px;">
        <small style="color: #718096;">Generated automatically by your Daily News AI Agent.</small>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.send_message(msg)
    print("Daily email dispatched successfully.")


if __name__ == "__main__":
    raw_news = fetch_top_news(limit=10)
    summary = generate_summary(raw_news)
    send_email(summary)
