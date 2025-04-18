import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

def analyze_post_engagement(posts_df):
    """
    Analyzes engagement metrics across different types of posts.
    
    Args:
        posts_df (pd.DataFrame): DataFrame containing post data
        
    Returns:
        pd.Series: Average engagement by post type
    """
    if posts_df.empty:
        return pd.Series()
    
    # Average engagement by post type
    engagement_by_type = posts_df.groupby('type')['engagement'].mean().sort_values(ascending=False)
    return engagement_by_type

def analyze_posting_patterns(posts_df):
    """
    Analyzes posting patterns and their correlation with engagement.
    
    Args:
        posts_df (pd.DataFrame): DataFrame containing post data
        
    Returns:
        pd.Series: Average engagement by hour of day
    """
    if posts_df.empty or 'time' not in posts_df.columns:
        return pd.Series()
    
    # Extract hour from time
    try:
        posts_df['hour'] = posts_df['time'].apply(lambda x: int(x.split(':')[0]))
        
        # Average engagement by hour
        engagement_by_hour = posts_df.groupby('hour')['engagement'].mean()
        return engagement_by_hour
    except:
        # If time format is inconsistent, return empty series
        return pd.Series()

def analyze_content_themes(posts_df):
    """
    Analyzes content themes and their effectiveness.
    
    Args:
        posts_df (pd.DataFrame): DataFrame containing post data
        
    Returns:
        dict: Analysis of content themes and their engagement
    """
    if posts_df.empty:
        return {}
    
    theme_analysis = {}
    
    # Analyze by content theme
    if 'theme' in posts_df.columns:
        theme_engagement = posts_df.groupby('theme')['engagement'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        
        for theme, data in theme_engagement.iterrows():
            avg_engagement = data['mean']
            count = data['count']
            
            # Generate observations based on engagement
            if avg_engagement > posts_df['engagement'].mean() * 1.2:
                observation = f"High engagement ({avg_engagement:.1f}). Consider creating more content on this theme."
            elif avg_engagement < posts_df['engagement'].mean() * 0.8:
                observation = f"Low engagement ({avg_engagement:.1f}). This theme may not resonate with your audience."
            else:
                observation = f"Average engagement ({avg_engagement:.1f}). Consistent performer."
                
            theme_analysis[theme] = {
                'avg_engagement': avg_engagement,
                'post_count': count,
                'observation': observation
            }
    
    # Analyze by content length
    if 'content_length_type' in posts_df.columns:
        length_engagement = posts_df.groupby('content_length_type')['engagement'].mean().sort_values(ascending=False)
        
        for length_type, avg_engagement in length_engagement.items():
            if length_type not in theme_analysis:
                theme_analysis[length_type] = {}
                
            if avg_engagement > posts_df['engagement'].mean() * 1.1:
                observation = f"{length_type.title()} posts perform well ({avg_engagement:.1f})"
            elif avg_engagement < posts_df['engagement'].mean() * 0.9:
                observation = f"{length_type.title()} posts underperform ({avg_engagement:.1f})"
            else:
                observation = f"{length_type.title()} posts have average performance ({avg_engagement:.1f})"
                
            theme_analysis[f"{length_type} content"] = {
                'avg_engagement': avg_engagement,
                'observation': observation
            }
    
    # Analyze posts with hashtags vs without
    if 'has_hashtags' in posts_df.columns:
        hashtag_engagement = posts_df.groupby('has_hashtags')['engagement'].mean()
        
        if True in hashtag_engagement and False in hashtag_engagement:
            with_hashtags = hashtag_engagement[True]
            without_hashtags = hashtag_engagement[False]
            
            if with_hashtags > without_hashtags * 1.1:
                observation = f"Posts with hashtags perform better ({with_hashtags:.1f} vs {without_hashtags:.1f})"
            elif without_hashtags > with_hashtags * 1.1:
                observation = f"Posts without hashtags perform better ({without_hashtags:.1f} vs {with_hashtags:.1f})"
            else:
                observation = f"Hashtags don't significantly impact engagement ({with_hashtags:.1f} vs {without_hashtags:.1f})"
                
            theme_analysis['hashtag usage'] = {
                'with_hashtags': with_hashtags,
                'without_hashtags': without_hashtags,
                'observation': observation
            }
    
    return theme_analysis

def get_optimal_posting_time(posts_df):
    """
    Determines the optimal posting time based on engagement patterns.
    
    Args:
        posts_df (pd.DataFrame): DataFrame containing post data
        
    Returns:
        str: Recommended posting time
    """
    if posts_df.empty or 'time' not in posts_df.columns:
        return "Not enough data to determine optimal posting time"
    
    try:
        # Extract hour from time
        posts_df['hour'] = posts_df['time'].apply(lambda x: int(x.split(':')[0]))
        
        # Get average engagement by hour
        engagement_by_hour = posts_df.groupby('hour')['engagement'].mean()
        
        if not engagement_by_hour.empty:
            # Find hour with highest engagement
            best_hour = engagement_by_hour.idxmax()
            
            # Format as a readable time
            if best_hour < 12:
                time_str = f"{best_hour}:00 AM"
            elif best_hour == 12:
                time_str = "12:00 PM"
            else:
                time_str = f"{best_hour-12}:00 PM"
                
            return time_str
        
        return "Not enough data to determine optimal posting time"
    except:
        return "Error analyzing posting times"

def extract_hashtags(posts_df):
    """
    Extracts and analyzes hashtag usage from posts.
    
    Args:
        posts_df (pd.DataFrame): DataFrame containing post data
        
    Returns:
        list: Popular hashtags and their frequency
    """
    if posts_df.empty or 'content' not in posts_df.columns:
        return []
    
    # Extract hashtags from content
    all_hashtags = []
    
    for content in posts_df['content']:
        # Find all hashtags in the content
        if isinstance(content, str):
            hashtags = [tag.strip().lower() for tag in content.split() if tag.startswith('#')]
            all_hashtags.extend(hashtags)
    
    # Count hashtag frequency
    hashtag_counts = Counter(all_hashtags)
    
    # Return most common hashtags
    return hashtag_counts.most_common(20)

def analyze_engagement_factors(posts_df):
    """
    Analyzes factors that contribute to higher engagement.
    
    Args:
        posts_df (pd.DataFrame): DataFrame containing post data
        
    Returns:
        dict: Factors that correlate with higher engagement
    """
    if posts_df.empty:
        return {}
    
    factors = {}
    
    # Analyze post length vs engagement
    if 'content_length' in posts_df.columns:
        # Bin post lengths
        posts_df['length_bin'] = pd.cut(
            posts_df['content_length'], 
            bins=[0, 100, 250, 500, 1000, 2000],
            labels=['Very Short', 'Short', 'Medium', 'Long', 'Very Long']
        )
        
        length_engagement = posts_df.groupby('length_bin')['engagement'].mean().sort_values(ascending=False)
        factors['content_length'] = {
            'best': length_engagement.index[0],
            'worst': length_engagement.index[-1],
            'data': length_engagement.to_dict()
        }
    
    # Boolean features analysis
    bool_features = ['has_hashtags', 'has_links', 'has_questions', 'has_mentions']
    
    for feature in bool_features:
        if feature in posts_df.columns:
            feature_engagement = posts_df.groupby(feature)['engagement'].mean()
            
            if True in feature_engagement and False in feature_engagement:
                feature_impact = (feature_engagement[True] / feature_engagement[False] - 1) * 100
                
                factors[feature] = {
                    'with': feature_engagement[True],
                    'without': feature_engagement[False],
                    'impact_percent': feature_impact
                }
    
    return factors
