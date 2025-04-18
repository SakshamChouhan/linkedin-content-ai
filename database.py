import os
import sqlite3
import pandas as pd
from datetime import datetime

# Database file path
DB_FILE = 'linkedin_data.db'

def initialize_database():
    """
    Initializes the SQLite database with necessary tables.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    
    # Profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        profile_url TEXT PRIMARY KEY,
        username TEXT,
        name TEXT,
        headline TEXT,
        location TEXT,
        connections INTEGER,
        avg_engagement REAL,
        last_updated TIMESTAMP
    )
    ''')
    
    # Posts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_url TEXT,
        date TEXT,
        time TEXT,
        content TEXT,
        type TEXT,
        theme TEXT,
        content_length INTEGER,
        content_length_type TEXT,
        likes INTEGER,
        comments INTEGER,
        shares INTEGER,
        engagement REAL,
        has_hashtags BOOLEAN,
        has_links BOOLEAN,
        has_questions BOOLEAN,
        has_mentions BOOLEAN,
        FOREIGN KEY (profile_url) REFERENCES profiles(profile_url)
    )
    ''')
    
    # Generated posts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS generated_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        topic TEXT,
        tone TEXT,
        include_cta BOOLEAN,
        include_hashtags BOOLEAN,
        feedback TEXT,
        generation_time TIMESTAMP,
        scheduled_time TIMESTAMP NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def save_profile(profile_data):
    """
    Saves profile data to the database.
    
    Args:
        profile_data (dict): Profile data to save
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Insert or update profile
    cursor.execute('''
    INSERT OR REPLACE INTO profiles 
    (profile_url, username, name, headline, location, connections, avg_engagement, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile_data['url'],
        profile_data['username'],
        profile_data['name'],
        profile_data.get('headline', ''),
        profile_data.get('location', ''),
        profile_data.get('connections', 0),
        profile_data.get('avg_engagement', 0),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # Save posts
    if 'posts' in profile_data and profile_data['posts']:
        for post in profile_data['posts']:
            cursor.execute('''
            INSERT INTO posts
            (profile_url, date, time, content, type, theme, content_length, content_length_type,
            likes, comments, shares, engagement, has_hashtags, has_links, has_questions, has_mentions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile_data['url'],
                post.get('date', ''),
                post.get('time', ''),
                post.get('content', ''),
                post.get('type', ''),
                post.get('theme', ''),
                post.get('content_length', 0),
                post.get('content_length_type', ''),
                post.get('likes', 0),
                post.get('comments', 0),
                post.get('shares', 0),
                post.get('engagement', 0),
                post.get('has_hashtags', False),
                post.get('has_links', False),
                post.get('has_questions', False),
                post.get('has_mentions', False)
            ))
    
    conn.commit()
    conn.close()

def get_profiles():
    """
    Retrieves all profiles from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing profile data
    """
    conn = sqlite3.connect(DB_FILE)
    
    query = "SELECT * FROM profiles"
    profiles_df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    return profiles_df

def get_posts():
    """
    Retrieves all posts from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing post data
    """
    conn = sqlite3.connect(DB_FILE)
    
    query = "SELECT * FROM posts"
    posts_df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    return posts_df

def save_generated_post(content, topic, tone, include_cta, include_hashtags, feedback='neutral', scheduled_time=None):
    """
    Saves a generated post to the database.
    
    Args:
        content (str): Post content
        topic (str): Post topic
        tone (str): Post tone
        include_cta (bool): Whether post includes CTA
        include_hashtags (bool): Whether post includes hashtags
        feedback (str): User feedback on the post
        scheduled_time (str, optional): Scheduled posting time
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO generated_posts
    (content, topic, tone, include_cta, include_hashtags, feedback, generation_time, scheduled_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        content,
        topic,
        tone,
        include_cta,
        include_hashtags,
        feedback,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        scheduled_time
    ))
    
    conn.commit()
    conn.close()

def update_post_feedback(post_id, feedback):
    """
    Updates feedback for a generated post.
    
    Args:
        post_id (int): ID of the post
        feedback (str): User feedback
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE generated_posts
    SET feedback = ?
    WHERE id = ?
    ''', (feedback, post_id))
    
    conn.commit()
    conn.close()

def get_post_feedback():
    """
    Retrieves feedback data for generated posts.
    
    Returns:
        pd.DataFrame: DataFrame containing feedback data
    """
    conn = sqlite3.connect(DB_FILE)
    
    query = "SELECT * FROM generated_posts"
    feedback_df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    return feedback_df

def get_post_feedback_stats():
    """
    Analyzes feedback data to provide statistics.
    
    Returns:
        dict: Feedback statistics
    """
    feedback_df = get_post_feedback()
    
    if feedback_df.empty:
        return None
    
    # Basic stats
    total_posts = len(feedback_df)
    positive_feedback = len(feedback_df[feedback_df['feedback'] == 'positive'])
    positive_percentage = (positive_feedback / total_posts) * 100 if total_posts > 0 else 0
    
    # Tone effectiveness
    tone_effectiveness = {}
    if 'tone' in feedback_df.columns:
        for tone in feedback_df['tone'].unique():
            tone_posts = feedback_df[feedback_df['tone'] == tone]
            tone_positive = len(tone_posts[tone_posts['feedback'] == 'positive'])
            tone_total = len(tone_posts)
            tone_effectiveness[tone] = (tone_positive / tone_total) * 100 if tone_total > 0 else 0
    
    # Preferred tone
    preferred_tone = max(tone_effectiveness.items(), key=lambda x: x[1])[0] if tone_effectiveness else None
    
    # Feedback trend over time
    if 'generation_time' in feedback_df.columns:
        feedback_df['generation_date'] = pd.to_datetime(feedback_df['generation_time']).dt.date
        trend_data = feedback_df.groupby('generation_date')['feedback'].apply(
            lambda x: (x == 'positive').mean() * 100
        )
        feedback_trend = trend_data
    else:
        feedback_trend = pd.Series()
    
    # Return stats
    return {
        'total_posts': total_posts,
        'positive_feedback': positive_feedback,
        'positive_percentage': positive_percentage,
        'tone_effectiveness': tone_effectiveness,
        'preferred_tone': preferred_tone,
        'feedback_trend': feedback_trend
    }

def schedule_post(post_id, scheduled_time):
    """
    Schedules a post for publication.
    
    Args:
        post_id (int): ID of the post
        scheduled_time (str): Scheduled posting time
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE generated_posts
    SET scheduled_time = ?
    WHERE id = ?
    ''', (scheduled_time, post_id))
    
    conn.commit()
    conn.close()

def get_scheduled_posts():
    """
    Retrieves all scheduled posts.
    
    Returns:
        pd.DataFrame: DataFrame containing scheduled posts
    """
    conn = sqlite3.connect(DB_FILE)
    
    query = "SELECT * FROM generated_posts WHERE scheduled_time IS NOT NULL"
    scheduled_df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    return scheduled_df

def insert_sample_feedback():
    """
    Inserts sample feedback posts into the database, if no posts exist.
    This function provides demo data for the dashboard when there is no real feedback yet.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Check if there's any feedback already
    cursor.execute('SELECT COUNT(*) FROM generated_posts')
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return  # Do nothing if feedback already exists

    from datetime import datetime, timedelta
    now = datetime.now()
    sample_posts = [
        {
            "content": "Excited to share my thoughts on AI in marketing! The potential for personalization and customer insights is game-changing. What's your experience with AI tools in your marketing strategy? #AIMarketing #DigitalTransformation #MarketingTrends",
            "topic": "AI in Marketing",
            "tone": "Conversational",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": (now - timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Leadership isn't about having all the answers—it's about asking the right questions. Today I challenged my team to think differently about our quarterly goals, and the insights were invaluable. True growth comes from collaborative problem-solving. #Leadership #TeamDevelopment",
            "topic": "Leadership",
            "tone": "Inspirational",
            "include_cta": False,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": (now - timedelta(days=12)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "New research reveals that companies with diverse leadership teams outperform competitors by 35%. This data confirms what we already knew: diversity isn't just good ethics, it's good business. Here's a link to the full study. #DiversityInBusiness #Leadership",
            "topic": "Diversity in Business",
            "tone": "Educational",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "negative",
            "generation_time": (now - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Just released our comprehensive guide to remote work best practices. After 2 years of research across 150+ companies, we've identified the key factors that make remote teams successful. Download now (link in comments). #RemoteWork #FutureOfWork #Productivity",
            "topic": "Remote Work",
            "tone": "Professional",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": (now - timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Our Q3 webinar series kicks off next week! Join industry experts as we explore emerging technologies reshaping finance. Reserve your spot now—spaces are limited. #FinTech #DigitalBanking #Innovation",
            "topic": "FinTech Webinar",
            "tone": "Promotional",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "neutral",
            "generation_time": (now - timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Thrilled to announce our partnership with Green Solutions to reduce our carbon footprint by 40% over the next two years. Sustainability isn't just a goal—it's our responsibility. #Sustainability #ClimateAction",
            "topic": "Sustainability",
            "tone": "Inspirational",
            "include_cta": False,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": (now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Data privacy matters more than ever. Our new white paper examines how regulations like GDPR and CCPA are impacting global businesses and provides actionable compliance strategies. Check it out and share your thoughts! #DataPrivacy #Compliance #GDPR",
            "topic": "Data Privacy",
            "tone": "Educational",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Just completed the Advanced Business Strategy certification! Grateful for the opportunity to expand my knowledge and connect with amazing professionals in the program. What professional development are you focusing on this quarter? #ProfessionalDevelopment #LifelongLearning",
            "topic": "Professional Development",
            "tone": "Conversational",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Breaking: Our new mobile app launches today! After months of user testing and refinement, we're proud to deliver a seamless experience that will transform how you manage your workflow. Download now from the App Store or Google Play. #ProductLaunch #Innovation #MobileApp",
            "topic": "Product Launch",
            "tone": "Promotional",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "negative",
            "generation_time": now.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "content": "Honored to be speaking at next month's Tech Forward Conference on 'Building Ethical AI Systems.' If you're attending, let's connect! #AI #TechEthics #Conference",
            "topic": "AI Ethics",
            "tone": "Professional",
            "include_cta": True,
            "include_hashtags": True,
            "feedback": "positive",
            "generation_time": now.strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    for post in sample_posts:
        cursor.execute(
            '''
            INSERT INTO generated_posts
            (content, topic, tone, include_cta, include_hashtags, feedback, generation_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                post["content"],
                post["topic"],
                post["tone"],
                post["include_cta"],
                post["include_hashtags"],
                post["feedback"],
                post["generation_time"]
            )
        )
    conn.commit()
    conn.close()
