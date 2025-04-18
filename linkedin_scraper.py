import re
import time
import random
import pandas as pd
from datetime import datetime, timedelta
import trafilatura
from utils import parse_url, clean_text

# LinkedIn selectors and patterns for scraping
LINKEDIN_POST_PATTERN = r'(\d+) (likes|comments|reactions)'
DATE_PATTERN = r'(\d+)([hd]) ago'

def scrape_linkedin_profile(profile_url):
    """
    Scrapes a LinkedIn profile to extract posts and engagement data.
    
    Args:
        profile_url (str): URL of the LinkedIn profile to scrape
        
    Returns:
        dict: Profile data including posts and engagement metrics
    """
    try:
        # Extract username from URL for identification
        username = parse_url(profile_url)
        
        # In a real implementation, we would use Selenium to log in and scrape
        # For this assignment, we'll simulate the scraped data
        
        # Simulate profile data
        profile_data = {
            'url': profile_url,
            'username': username,
            'name': username.replace('-', ' ').title(),
            'headline': f"Professional at {random.choice(['Tech Company', 'Innovation Corp', 'Digital Solutions'])}",
            'location': random.choice(['San Francisco, CA', 'New York, NY', 'Bangalore, India', 'London, UK']),
            'connections': random.randint(500, 5000),
            'posts': [],
            'avg_engagement': 0
        }
        
        # Simulate post data
        num_posts = random.randint(15, 30)
        total_engagement = 0
        
        for i in range(num_posts):
            # Random date within the last 30 days
            days_ago = random.randint(0, 30)
            post_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            post_time = f"{random.randint(7, 19)}:{random.choice(['00', '15', '30', '45'])}"
            
            # Engagement metrics
            likes = random.randint(10, 500)
            comments = random.randint(0, 50)
            shares = random.randint(0, 20)
            engagement_score = likes + (comments * 3) + (shares * 5)
            total_engagement += engagement_score
            
            # Post type and content
            post_type = random.choice(['text', 'article', 'image', 'video', 'poll', 'document'])
            
            # Simulated content themes
            themes = [
                "professional development",
                "industry trends",
                "personal achievement",
                "company news",
                "leadership insights",
                "tech innovation",
                "career advice"
            ]
            
            content_lengths = {
                'short': (50, 200),
                'medium': (201, 500),
                'long': (501, 1000)
            }
            
            content_length_type = random.choice(list(content_lengths.keys()))
            min_len, max_len = content_lengths[content_length_type]
            
            # Generate simulated post content
            theme = random.choice(themes)
            if post_type == 'text':
                content = f"Post about {theme} with {content_length_type} content length. "
                content += "This is simulated post content to represent what would be scraped from LinkedIn. "
                content += f"This post has {likes} likes, {comments} comments, and {shares} shares."
                content = content.ljust(random.randint(min_len, max_len))
            else:
                content = f"{post_type.title()} post about {theme}. "
                content += f"Media post with {content_length_type} description. "
                content += f"This post has {likes} likes, {comments} comments, and {shares} shares."
                content = content.ljust(random.randint(min_len, max_len))
            
            # Add hashtags sometimes
            if random.random() > 0.3:
                num_hashtags = random.randint(1, 5)
                hashtags = [f"#{theme.replace(' ', '')}", f"#{post_type}", "#LinkedIn", "#Professional", "#Career", "#Innovation"]
                content += " " + " ".join(random.sample(hashtags, min(num_hashtags, len(hashtags))))
            
            # Create post object
            post = {
                'date': post_date,
                'time': post_time,
                'content': content,
                'type': post_type,
                'theme': theme,
                'content_length': len(content),
                'content_length_type': content_length_type,
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'engagement': engagement_score,
                'has_hashtags': '#' in content,
                'has_links': 'http' in content,
                'has_questions': '?' in content,
                'has_mentions': '@' in content
            }
            
            profile_data['posts'].append(post)
        
        # Calculate average engagement
        if num_posts > 0:
            profile_data['avg_engagement'] = total_engagement / num_posts
        
        return profile_data
    
    except Exception as e:
        print(f"Error scraping LinkedIn profile: {str(e)}")
        return None


def scrape_multiple_profiles(profile_urls):
    """
    Scrapes multiple LinkedIn profiles and combines the data.
    
    Args:
        profile_urls (list): List of LinkedIn profile URLs to scrape
        
    Returns:
        pd.DataFrame: Combined post data from all profiles
    """
    all_posts = []
    
    for url in profile_urls:
        try:
            profile_data = scrape_linkedin_profile(url)
            if profile_data and 'posts' in profile_data:
                # Add profile information to each post
                for post in profile_data['posts']:
                    post['profile_url'] = url
                    post['profile_name'] = profile_data['name']
                    all_posts.append(post)
                
                # Add some delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"Error scraping profile {url}: {str(e)}")
    
    # Convert to DataFrame
    if all_posts:
        return pd.DataFrame(all_posts)
    else:
        return pd.DataFrame()
