import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from linkedin_scraper import scrape_linkedin_profile
from data_analyzer import (
    analyze_post_engagement,
    analyze_posting_patterns,
    analyze_content_themes,
    get_optimal_posting_time
)
from content_generator import generate_post, update_feedback_preferences
from database import (
    initialize_database,
    get_posts,
    save_generated_post,
    update_post_feedback,
    get_post_feedback_stats,
    get_post_feedback,
    insert_sample_feedback
)
from utils import load_profile_data, parse_url

# Page configuration
st.set_page_config(
    page_title="LinkedIn Content Creator AI",
    page_icon="📊",
    layout="wide"
)

# Initialize the database
initialize_database()

# Load target profile data
TARGET_PROFILE = "https://www.linkedin.com/in/archit-anand/"
COMPETITOR_PROFILES = [
    "https://www.linkedin.com/in/aarongolbin/",
    "https://www.linkedin.com/in/robertsch%C3%B6ne/",
    "https://www.linkedin.com/in/jaspar-carmichael-jack/"
]

# Main page title and introduction
st.title("LinkedIn Content Creator AI")
st.markdown("""
This tool helps you analyze LinkedIn profiles, identify content trends, and generate optimized posts.
""")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Profile Analysis", "Content Insights", "Post Generator", "Feedback Dashboard"]
)

if page == "Profile Analysis":
    st.header("LinkedIn Profile Analysis")
    
    # Profile selection
    profile_option = st.selectbox(
        "Select a profile to analyze",
        [TARGET_PROFILE] + COMPETITOR_PROFILES
    )
    
    # Scrape and analyze button
    if st.button("Scrape and Analyze Profile"):
        with st.spinner("Scraping profile data... (This may take a moment)"):
            try:
                profile_data = scrape_linkedin_profile(profile_option)
                if profile_data:
                    # Save profile data to database
                    from database import save_profile
                    save_profile(profile_data)
                    
                    st.success(f"Successfully scraped profile: {profile_data['name']}")
                    
                    # Display basic profile info
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Profile Information")
                        st.write(f"**Name:** {profile_data['name']}")
                        st.write(f"**Headline:** {profile_data['headline']}")
                        st.write(f"**Location:** {profile_data['location']}")
                        st.write(f"**Connections:** {profile_data['connections']}")
                    
                    with col2:
                        st.subheader("Activity Overview")
                        st.write(f"**Total Posts:** {len(profile_data['posts'])}")
                        st.write(f"**Average Engagement:** {profile_data['avg_engagement']:.1f}")
                    
                    # Display recent posts
                    st.subheader("Recent Posts")
                    posts_df = pd.DataFrame(profile_data['posts'])
                    st.dataframe(posts_df)
                    
                    st.info("Profile data has been saved. You can now view insights in the 'Content Insights' section.")
                else:
                    st.error("Failed to retrieve profile data. Please try again.")
            except Exception as e:
                st.error(f"Error scraping profile: {str(e)}")
    
    # Display already scraped profiles
    st.subheader("Previously Analyzed Profiles")
    scraped_profiles = load_profile_data()
    if scraped_profiles.empty:
        st.info("No profiles have been analyzed yet.")
    else:
        st.dataframe(scraped_profiles)

elif page == "Content Insights":
    st.header("Content Insights & Trends")
    
    # Get stored data
    posts_df = get_posts()
    
    if posts_df.empty:
        st.warning("No data available. Please scrape LinkedIn profiles first.")
    else:
        # Engagement analysis
        st.subheader("Engagement Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 6))
            engagement_data = analyze_post_engagement(posts_df)
            engagement_data.plot(kind='bar', ax=ax)
            plt.title("Average Engagement by Content Type")
            plt.ylabel("Engagement Score")
            plt.xlabel("Content Type")
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.write("Key Insights:")
            content_themes = analyze_content_themes(posts_df)
            for content_type, stats in content_themes.items():
                if 'observation' in stats:
                    st.write(f"**{content_type}**: {stats['observation']}")
                elif 'avg_engagement' in stats:
                    st.write(f"**{content_type}**: Average engagement: {stats['avg_engagement']:.1f}")
        
        # Posting patterns
        st.subheader("Posting Patterns")
        fig, ax = plt.subplots(figsize=(10, 6))
        time_data = analyze_posting_patterns(posts_df)
        time_data.plot(kind='line', marker='o', ax=ax)
        plt.title("Posting Time vs Engagement")
        plt.ylabel("Average Engagement")
        plt.xlabel("Hour of Day")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
        
        optimal_time = get_optimal_posting_time(posts_df)
        st.info(f"**Optimal posting time**: {optimal_time}")
        
        # Content length analysis
        st.subheader("Content Length Analysis")
        fig, ax = plt.subplots(figsize=(10, 6))
        posts_df['content_length'] = posts_df['content'].apply(len)
        posts_df.plot.scatter(x='content_length', y='engagement', ax=ax, alpha=0.6)
        plt.title("Content Length vs. Engagement")
        plt.xlabel("Content Length (characters)")
        plt.ylabel("Engagement")
        plt.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig)

elif page == "Post Generator":
    st.header("AI Post Generator")
    
    # Topic input
    topic = st.text_input("Enter a topic or theme for your post:")
    
    # Additional prompts
    with st.expander("Advanced Options"):
        tone = st.select_slider(
            "Select tone:",
            options=["Professional", "Conversational", "Inspirational", "Educational", "Promotional"]
        )
        include_cta = st.checkbox("Include a call-to-action", value=True)
        max_length = st.slider("Maximum post length", 100, 1000, 500)
        include_hashtags = st.checkbox("Include hashtags", value=True)
        num_hashtags = st.slider("Number of hashtags", 1, 10, 3) if include_hashtags else 0
    
    # Generate post button
    if st.button("Generate Post"):
        if not topic:
            st.warning("Please enter a topic for your post.")
        else:
            with st.spinner("Generating post variations..."):
                try:
                    post_variations = generate_post(
                        topic=topic,
                        tone=tone,
                        include_cta=include_cta,
                        max_length=max_length,
                        include_hashtags=include_hashtags,
                        num_hashtags=num_hashtags
                    )
                    
                    if post_variations:
                        # Display post variations with feedback options
                        for i, post in enumerate(post_variations):
                            st.subheader(f"Variation {i+1}")
                            st.markdown(post["content"].replace('\n', '<br>'), unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"👍 Like", key=f"like_{i}"):
                                    save_generated_post(post["content"], topic, tone, include_cta, include_hashtags, feedback="positive")
                                    st.success("Post saved with positive feedback!")
                                    st.balloons()
                            with col2:
                                if st.button(f"👎 Dislike", key=f"dislike_{i}"):
                                    save_generated_post(post["content"], topic, tone, include_cta, include_hashtags, feedback="negative")
                                    st.info("Post saved with negative feedback. We'll improve next time!")
                            with col3:
                                if st.button(f"💾 Save", key=f"save_{i}"):
                                    save_generated_post(post["content"], topic, tone, include_cta, include_hashtags, feedback="neutral")
                                    st.success("Post saved!")
                    else:
                        st.error("Failed to generate posts. Please try again.")
                except Exception as e:
                    st.error(f"Error generating posts: {str(e)}")

elif page == "Feedback Dashboard":
    st.header("Feedback & Learning Dashboard")
    
    # Get feedback data
    feedback_df = get_post_feedback()
    feedback_stats = get_post_feedback_stats()
    
    # If no feedback, insert sample feedback (only if database is empty)
    if feedback_df.empty:
        # Try to insert sample feedback
        insert_sample_feedback()
        feedback_df = get_post_feedback()
        feedback_stats = get_post_feedback_stats()
    
    # Display feedback overview
    st.subheader("Feedback Overview")
    if feedback_stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Posts Generated", feedback_stats["total_posts"])
        with col2:
            st.metric("Positive Feedback", f"{feedback_stats['positive_percentage']:.1f}%")
        with col3:
            st.metric("Most Effective Tone", feedback_stats["preferred_tone"])
        
        # Display charts
        st.subheader("Feedback by Content Characteristics")
        
        # Tone effectiveness chart
        tone_data = feedback_stats["tone_effectiveness"]
        if tone_data:
            fig, ax = plt.subplots(figsize=(10, 5))
            pd.Series(tone_data).plot(kind='bar', ax=ax)
            plt.title("Positive Feedback Rate by Tone")
            plt.ylabel("Positive Feedback Rate (%)")
            plt.xlabel("Tone")
            plt.tight_layout()
            st.pyplot(fig)
        
        # Feedback trends over time
        st.subheader("Feedback Trends Over Time")
        if "feedback_trend" in feedback_stats and not feedback_stats["feedback_trend"].empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            feedback_stats["feedback_trend"].plot(ax=ax)
            plt.title("Feedback Trends Over Time")
            plt.ylabel("Positive Feedback Rate (%)")
            plt.xlabel("Generation Date")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            st.pyplot(fig)
        
        # Display actual posts with feedback
        st.subheader("Recent Generated Posts")
        
        # Create tabs for different feedback types
        tab1, tab2, tab3 = st.tabs(["All Posts", "Positive Feedback", "Needs Improvement"])
        
        with tab1:
            if not feedback_df.empty:
                for i, row in feedback_df.sort_values('generation_time', ascending=False).head(5).iterrows():
                    st.markdown(f"**Topic: {row['topic']}** | Tone: {row['tone']} | Feedback: {row['feedback']}")
                    st.markdown(f"{row['content']}")
                    st.markdown("---")
            else:
                st.info("No posts available")
        
        with tab2:
            positive_df = feedback_df[feedback_df['feedback'] == 'positive']
            if not positive_df.empty:
                for i, row in positive_df.sort_values('generation_time', ascending=False).head(5).iterrows():
                    st.markdown(f"**Topic: {row['topic']}** | Tone: {row['tone']} | 👍 Positive Feedback")
                    st.markdown(f"{row['content']}")
                    st.markdown("---")
            else:
                st.info("No posts with positive feedback yet")
        
        with tab3:
            negative_df = feedback_df[feedback_df['feedback'] == 'negative']
            if not negative_df.empty:
                for i, row in negative_df.sort_values('generation_time', ascending=False).head(5).iterrows():
                    st.markdown(f"**Topic: {row['topic']}** | Tone: {row['tone']} | 👎 Needs Improvement")
                    st.markdown(f"{row['content']}")
                    st.markdown("---")
            else:
                st.info("No posts with negative feedback yet")
        
        # Topic effectiveness
        st.subheader("Topic Effectiveness")
        if not feedback_df.empty and 'topic' in feedback_df.columns:
            topic_data = {}
            for topic in feedback_df['topic'].unique():
                topic_posts = feedback_df[feedback_df['topic'] == topic]
                topic_positive = len(topic_posts[topic_posts['feedback'] == 'positive'])
                topic_total = len(topic_posts)
                topic_data[topic] = (topic_positive / topic_total) * 100 if topic_total > 0 else 0
            
            if topic_data:
                fig, ax = plt.subplots(figsize=(10, 5))
                pd.Series(topic_data).sort_values(ascending=False).plot(kind='bar', ax=ax)
                plt.title("Positive Feedback Rate by Topic")
                plt.ylabel("Positive Feedback Rate (%)")
                plt.xlabel("Topic")
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
        
    else:
        st.info("No feedback data available yet. Generate and rate some posts to see insights.")

# Footer
st.markdown("---")
st.markdown("LinkedIn Content Creator AI © 2024")
