import os
import json
import random
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from database import get_post_feedback, get_posts

# Initialize Google's Gemini AI
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Global preferences based on user feedback
user_preferences = {
    'preferred_tone': 'Conversational',
    'optimal_length': 'medium',
    'preferred_content_types': ['professional development', 'industry trends'],
    'hashtag_preference': True
}

def generate_post(topic, tone="Conversational", include_cta=True, max_length=500, include_hashtags=True, num_hashtags=3):
    """
    Generates LinkedIn post variations using Google's Gemini AI.
    
    Args:
        topic (str): Topic or theme for the post
        tone (str): Desired tone of the post
        include_cta (bool): Whether to include a call-to-action
        max_length (int): Maximum length of the post
        include_hashtags (bool): Whether to include hashtags
        num_hashtags (int): Number of hashtags to include
        
    Returns:
        list: List of generated post variations
    """
    try:
        # Get engagement data to inform the prompt
        posts_df = get_posts()
        feedback_data = get_post_feedback()
        
        # Analyze what works well
        insights = ""
        if not posts_df.empty:
            # Find top performing content types
            if 'theme' in posts_df.columns:
                top_themes = posts_df.groupby('theme')['engagement'].mean().nlargest(3).index.tolist()
                insights += f"Top performing themes: {', '.join(top_themes)}. "
            
            # Check if questions perform well
            if 'has_questions' in posts_df.columns:
                question_performance = posts_df.groupby('has_questions')['engagement'].mean()
                if True in question_performance and False in question_performance:
                    if question_performance[True] > question_performance[False]:
                        insights += "Posts with questions perform better. "
            
            # Check optimal length
            if 'content_length_type' in posts_df.columns:
                length_performance = posts_df.groupby('content_length_type')['engagement'].mean().nlargest(1).index[0]
                insights += f"Posts with {length_performance} length perform best. "
        
        # Configure Gemini model
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 1500,
        }
        
        # Setting up the model with Gemini-1.5-pro
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        # System instruction and prompt
        system_instruction = "You are a LinkedIn content expert who creates engaging posts that drive high engagement."
        
        # Prompt engineering for LinkedIn posts
        prompt = f"""
        {system_instruction}
        
        Create 3 variations of a LinkedIn post about {topic}.
        
        Guidelines:
        - Tone: {tone}
        - Maximum length: {max_length} characters
        - {include_cta and 'Include a call-to-action' or 'No call-to-action needed'}
        - {include_hashtags and f'Include {num_hashtags} relevant hashtags' or 'No hashtags needed'}
        
        Insights from performance data:
        {insights}
        
        Make sure the posts are professional, engaging, and optimized for LinkedIn's algorithm.
        Each variation should be different in structure and approach while maintaining the core message.
        
        Return the posts in this JSON format:
        {{
          "posts": [
            {{
              "content": "Post content here",
              "estimated_engagement": 0-100
            }},
            ...more posts
          ]
        }}
        
        Only return the JSON, nothing else. Make sure the JSON is properly formatted and valid.
        """
        
        # Generate content with Gemini
        response = model.generate_content(prompt)
        
        # Parse the response
        try:
            result = json.loads(response.text)
            return result["posts"]
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response text
            import re
            json_pattern = r'({[\s\S]*})'
            match = re.search(json_pattern, response.text)
            
            if match:
                result = json.loads(match.group(1))
                return result["posts"]
            else:
                raise ValueError("Could not parse JSON from Gemini response")
    
    except Exception as e:
        print(f"Error generating posts: {str(e)}")
        # Fallback to a simple generation method if Gemini fails
        fallback_posts = [
            {
                "content": f"Here's my thoughts on {topic}. What do you think? #LinkedIn #Professional",
                "estimated_engagement": 50
            },
            {
                "content": f"I've been thinking about {topic} lately and wanted to share my perspective. Would love to hear your thoughts! #Career #Insights",
                "estimated_engagement": 45
            }
        ]
        return fallback_posts

def update_feedback_preferences(feedback_data):
    """
    Updates user preferences based on feedback data.
    
    Args:
        feedback_data (pd.DataFrame): Feedback data on generated posts
        
    Returns:
        dict: Updated user preferences
    """
    global user_preferences
    
    if feedback_data.empty:
        return user_preferences
    
    # Only consider posts with positive feedback
    positive_feedback = feedback_data[feedback_data['feedback'] == 'positive']
    
    if not positive_feedback.empty:
        # Update tone preference
        if 'tone' in positive_feedback.columns:
            tone_counts = positive_feedback['tone'].value_counts()
            if not tone_counts.empty:
                user_preferences['preferred_tone'] = tone_counts.index[0]
        
        # Update length preference
        if 'content' in positive_feedback.columns:
            positive_feedback['content_length'] = positive_feedback['content'].apply(len)
            avg_length = positive_feedback['content_length'].mean()
            
            if avg_length < 200:
                user_preferences['optimal_length'] = 'short'
            elif avg_length < 500:
                user_preferences['optimal_length'] = 'medium'
            else:
                user_preferences['optimal_length'] = 'long'
        
        # Update hashtag preference
        if 'include_hashtags' in positive_feedback.columns:
            hashtag_preference = positive_feedback['include_hashtags'].mean() > 0.5
            user_preferences['hashtag_preference'] = hashtag_preference
    
    return user_preferences

def generate_hashtags(topic, num_hashtags=3):
    """
    Generates relevant hashtags for a given topic using Google's Gemini AI.
    
    Args:
        topic (str): Topic to generate hashtags for
        num_hashtags (int): Number of hashtags to generate
        
    Returns:
        list: List of hashtags
    """
    try:
        # Configure Gemini model
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 200,
        }
        
        # Setting up the model with Gemini-1.5-pro
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        # System instruction and prompt
        prompt = f"""
        You are a social media hashtag expert.
        
        Generate {num_hashtags} relevant, professional LinkedIn hashtags for content about {topic}.
        Return only the hashtags (with # symbol) as a JSON array with a key called 'hashtags', without any explanation.
        
        Example: {{"hashtags": ["#Leadership", "#Innovation", "#TechTrends"]}}
        
        Only return the JSON, nothing else. Make sure the JSON is properly formatted and valid.
        """
        
        # Generate content with Gemini
        response = model.generate_content(prompt)
        
        # Parse the response
        try:
            result = json.loads(response.text)
            return result.get("hashtags", [])
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response text
            import re
            json_pattern = r'({[\s\S]*})'
            match = re.search(json_pattern, response.text)
            
            if match:
                result = json.loads(match.group(1))
                return result.get("hashtags", [])
            else:
                # Try to extract hashtags directly
                hashtag_pattern = r'#\w+'
                hashtags = re.findall(hashtag_pattern, response.text)
                if hashtags:
                    return hashtags[:num_hashtags]
                else:
                    raise ValueError("Could not parse hashtags from Gemini response")
    
    except Exception as e:
        print(f"Error generating hashtags: {str(e)}")
        # Fallback hashtags
        fallback_hashtags = [
            f"#{topic.replace(' ', '')}",
            "#LinkedIn",
            "#Professional"
        ]
        return fallback_hashtags[:num_hashtags]
