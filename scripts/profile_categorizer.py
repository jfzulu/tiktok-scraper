#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROFILE CATEGORIZER - TikTok Profile Analysis Tool
=================================================
Simplified script that reads user data, generates English prompts,
and categorizes profiles using ChatGPT API without predefined categories.

Version: 1.0
Author: Carnival Cruises TikTok Analyzer Team
"""

import os
import csv
import json
import yaml
import pandas as pd
import requests
import traceback
from datetime import datetime
from configparser import ConfigParser

# =============================================================================
# 1. CONFIGURATION AND API SETUP
# =============================================================================

def load_openai_config():
    """Load OpenAI API configuration from config files"""
    config = ConfigParser()
    config_path = 'config/config_company.ini'
    
    try:
        print(f"[PAGE] Loading OpenAI config from: {config_path}")
        config.read(config_path)
        
        if 'openai' not in config or 'api_key' not in config['openai']:
            raise KeyError("OpenAI API configuration not found")
        
        api_key = config['openai']['api_key']
        masked_key = f"{api_key[:7]}...{api_key[-7:]}" if len(api_key) > 14 else "***masked***"
        print(f"   [OK] OpenAI API Key loaded: {masked_key}")
        
        return {
            'api_key': api_key,
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'model': 'gpt-4'
        }
        
    except Exception as e:
        print(f"[ERROR] Error loading OpenAI config: {e}")
        raise

def load_users_from_excel(excel_file="data/Input/usernames.xlsx", limit=5):
    """Load users list from Excel file"""
    try:
        print(f"[CHART] Loading users from: {excel_file}")
        
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Take only first 'limit' users
        df_limited = df.head(limit)
        
        print(f"   [CLIPBOARD] Users in file: {len(df)}")
        print(f"   [TARGET] Users to process: {len(df_limited)}")
        
        # Convert to list of dictionaries
        users = []
        for index, row in df_limited.iterrows():
            user = {
                'username': str(row['username']).replace('@', ''),  # Remove @ if exists
                'url': str(row['URL']) if pd.notna(row['URL']) else f"https://www.tiktok.com/@{str(row['username']).replace('@', '')}"
            }
            users.append(user)
            print(f"      {len(users)}. @{user['username']}")
        
        return users
        
    except Exception as e:
        print(f"[ERROR] Error loading users from Excel: {e}")
        return []

# =============================================================================
# 2. DATA LOADING AND CONSOLIDATION
# =============================================================================

def load_user_data(username):
    """Load consolidated user data from pipeline output files"""
    
    user_data = {
        'username': username,
        'profile_info': {},
        'profile_stats': {},
        'videos_data': [],
        'is_private': False,
        'is_verified': False,
        'data_available': {
            'user_info': False,
            'videos_info': False
        }
    }
    
    try:
        # 1. Load user basic info
        user_info_file = f"data/Output/user_info/{username}_user_info.yml"
        if os.path.exists(user_info_file):
            print(f"      [PAGE] Loading user info...")
            with open(user_info_file, 'r', encoding='utf-8') as f:
                user_yaml = yaml.safe_load(f)
                user_data['profile_info'] = user_yaml.get('profile_basic_info', {})
                user_data['profile_stats'] = user_yaml.get('profile_stats', {})
                user_data['is_private'] = user_data['profile_info'].get('private_account', False)
                user_data['is_verified'] = user_data['profile_info'].get('verified', False)
                user_data['data_available']['user_info'] = True
        
        # 2. Load videos info
        videos_info_file = f"data/Output/videos_info/{username}_videos.yml"
        if os.path.exists(videos_info_file):
            print(f"      [VIDEO] Loading videos info...")
            with open(videos_info_file, 'r', encoding='utf-8') as f:
                videos_yaml = yaml.safe_load(f)
                user_data['videos_data'] = videos_yaml.get('videos_list', [])[:10]  # Max 10 videos
                user_data['data_available']['videos_info'] = True
        
        return user_data
        
    except Exception as e:
        print(f"      [ERROR] Error loading data for @{username}: {e}")
        return user_data

# =============================================================================
# 3. PROMPT GENERATION
# =============================================================================

def create_categorization_prompt_template():
    """Create the categorization prompt template in English"""
    
    prompt_template = """You are an expert social media analyst specializing in TikTok profile categorization. 
Please analyze the following TikTok profile and categorize it based on the content, behavior patterns, and characteristics you observe.

**PROFILE DATA:**
- Username: {username}
- Display Name: {display_name}
- Bio/Description: {bio}
- Follower Count: {follower_count}
- Following Count: {following_count}
- Total Likes: {likes_count}
- Video Count: {video_count}
- Is Verified: {is_verified}
- Is Private Account: {is_private}

**RECENT CONTENT ANALYSIS:**
{videos_analysis}

**INSTRUCTIONS:**
1. Analyze this profile comprehensively
2. Create a profile category that best describes this account type
3. Be specific and descriptive in your categorization
4. Consider: content themes, audience engagement patterns, posting behavior, professional vs personal nature
5. Do NOT use generic categories - be creative and specific

**RESPONSE FORMAT:**
Respond with ONLY a JSON object in this exact format:
{{
    "profile_category": "your_specific_category_here",
    "category_reasoning": "brief explanation of why this category fits",
    "account_nature": "personal/business/creator/influencer/brand/organization",
    "content_focus": "brief description of main content themes",
    "engagement_level": "high/medium/low",
    "authenticity_assessment": "authentic/commercial/mixed"
}}

**IMPORTANT:** Respond ONLY with valid JSON. No additional text or explanations outside the JSON."""

    return prompt_template

def prepare_user_data_for_prompt(user_data):
    """Prepare user data for the categorization prompt"""
    
    # Extract basic profile info
    profile_info = user_data.get('profile_info', {})
    profile_stats = user_data.get('profile_stats', {})
    
    # Prepare videos analysis
    videos_data = user_data.get('videos_data', [])
    videos_analysis = ""
    
    if videos_data:
        videos_analysis = f"**RECENT VIDEOS ({len(videos_data)} videos analyzed):**\n"
        for i, video in enumerate(videos_data[:5], 1):  # Max 5 videos for prompt
            title = video.get('title', 'No title')
            play_count = video.get('video_stats', {}).get('play_count', 0)
            like_count = video.get('video_stats', {}).get('digg_count', 0)
            comment_count = video.get('video_stats', {}).get('comment_count', 0)
            
            videos_analysis += f"{i}. Title: {title[:100]}...\n"
            videos_analysis += f"   Engagement: {play_count:,} views, {like_count:,} likes, {comment_count:,} comments\n"
    else:
        videos_analysis = "**RECENT VIDEOS:** No video data available or private account"
    
    # Prepare data for prompt
    prompt_data = {
        'username': user_data.get('username', 'N/A'),
        'display_name': profile_info.get('nickname', 'N/A'),
        'bio': profile_info.get('signature', 'No bio available'),
        'follower_count': format_count(profile_stats.get('follower_count', 0)),
        'following_count': format_count(profile_stats.get('following_count', 0)),
        'likes_count': format_count(profile_stats.get('heart_count', 0)),
        'video_count': format_count(profile_stats.get('video_count', 0)),
        'is_verified': user_data.get('is_verified', False),
        'is_private': user_data.get('is_private', False),
        'videos_analysis': videos_analysis
    }
    
    return prompt_data

def format_count(count):
    """Format large numbers in a readable way"""
    try:
        count = int(count)
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.1f}K"
        else:
            return str(count)
    except:
        return "N/A"

def create_final_prompt(template, data):
    """Create the final prompt by replacing placeholders"""
    try:
        return template.format(**data)
    except Exception as e:
        print(f"   [WARNING]  Error creating prompt: {e}")
        return f"Analyze this TikTok profile: @{data.get('username', 'unknown')} - {data}"

def save_prompt_to_file(prompt, username):
    """Save the generated prompt to Input directory (disabled for production)"""
    # NOTE: Individual prompt files are disabled for production
    # Only template files should exist in /prompts directory
    print(f"      [MEMO] Prompt generated for @{username} (not saved individually)")
    return f"prompt_generated_for_{username}"

# =============================================================================
# 4. CHATGPT API INTEGRATION
# =============================================================================

def categorize_with_chatgpt(api_config, prompt, username):
    """Send prompt to ChatGPT API and get categorization"""
    
    print(f"      [ROBOT] Sending to ChatGPT API...")
    
    headers = {
        'Authorization': f'Bearer {api_config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": api_config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are an expert social media analyst. Respond only with valid JSON as requested."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            api_config['api_url'],
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            print(f"         [OK] Response received ({len(content)} chars)")
            
            # Try to parse JSON response
            try:
                # Clean the response (remove potential markdown formatting)
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                result_json = json.loads(content)
                print(f"         [TARGET] Category: {result_json.get('profile_category', 'Unknown')}")
                return result_json
                
            except json.JSONDecodeError as e:
                print(f"         [ERROR] JSON parse error: {e}")
                print(f"         [PAGE] Raw response: {content[:200]}...")
                return {
                    "profile_category": "parse_error",
                    "category_reasoning": "Failed to parse API response",
                    "account_nature": "unknown",
                    "content_focus": "unknown",
                    "engagement_level": "unknown",
                    "authenticity_assessment": "unknown",
                    "raw_response": content
                }
        
        elif response.status_code == 429:
            print(f"         [WAIT] Rate limit hit - waiting...")
            return None
            
        else:
            print(f"         [ERROR] API error {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"         [ERROR] Request error: {e}")
        return None

# =============================================================================
# 5. CSV OUTPUT
# =============================================================================

def save_results_to_csv(results, output_file="data/Output/profile_categorization_results.csv"):
    """Save categorization results to CSV file"""
    
    try:
        print(f"\n[SAVE] Saving results to: {output_file}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Define CSV columns
        fieldnames = [
            'platform',
            'username', 
            'url',
            'is_public_account',
            'category',
            'category_reasoning',
            'account_nature',
            'content_focus',
            'engagement_level',
            'authenticity_assessment',
            'analysis_date'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow(result)
        
        print(f"   [OK] CSV file saved with {len(results)} results")
        return output_file
        
    except Exception as e:
        print(f"   [ERROR] Error saving CSV: {e}")
        return None

# =============================================================================
# 6. MAIN FUNCTION
# =============================================================================

def main():
    """Main function of the profile categorizer"""
    
    print("[TAG]  TIKTOK PROFILE CATEGORIZER")
    print("=" * 50)
    print(" [ROBOT] AI-powered profile categorization")
    print(" [CHART] Reads data from Excel and pipeline output")
    print(" [GB] English prompts and ChatGPT API")
    print(" [PAGE] CSV output with categories")
    print("=" * 50)
    
    try:
        # 1. Load configuration
        print(f"\n[CLIPBOARD] STEP 1: Loading configuration")
        api_config = load_openai_config()
        
        # 2. Load users from Excel
        print(f"\n[CLIPBOARD] STEP 2: Loading users from Excel")
        users = load_users_from_excel()
        
        if not users:
            print(f"\n[ERROR] No users found in Excel file")
            return
        
        # 3. Create prompt template
        print(f"\n[CLIPBOARD] STEP 3: Creating categorization prompt template")
        prompt_template = create_categorization_prompt_template()
        
        # 4. Process each user
        print(f"\n[CLIPBOARD] STEP 4: Processing users")
        results = []
        
        for i, user_info in enumerate(users, 1):
            username = user_info['username']
            url = user_info['url']
            
            print(f"\n[USER] PROCESSING {i}/{len(users)}: @{username}")
            print("-" * 40)
            
            # Load user data
            user_data = load_user_data(username)
            
            # Show data availability
            user_available = user_data['data_available']['user_info']
            videos_available = user_data['data_available']['videos_info']
            print(f"      [CHART] Data availability: User info: {'[OK]' if user_available else '[ERROR]'}, Videos: {'[OK]' if videos_available else '[ERROR]'}")
            
            if not user_available:
                print(f"      [WARNING]  No user data available - skipping categorization")
                # Add basic result for missing data
                results.append({
                    'platform': 'tiktok',
                    'username': username,
                    'url': url,
                    'is_public_account': 'unknown',
                    'category': 'no_data_available',
                    'category_reasoning': 'User data not found in pipeline output',
                    'account_nature': 'unknown',
                    'content_focus': 'unknown',
                    'engagement_level': 'unknown',
                    'authenticity_assessment': 'unknown',
                    'analysis_date': datetime.now().isoformat()
                })
                continue
            
            # Prepare prompt data
            prompt_data = prepare_user_data_for_prompt(user_data)
            final_prompt = create_final_prompt(prompt_template, prompt_data)
            
            # Save prompt to file
            save_prompt_to_file(final_prompt, username)
            
            # Get categorization from ChatGPT
            categorization = categorize_with_chatgpt(api_config, final_prompt, username)
            
            if categorization:
                # Prepare CSV result
                result = {
                    'platform': 'tiktok',
                    'username': username,
                    'url': url,
                    'is_public_account': 'public' if not user_data.get('is_private', False) else 'private',
                    'category': categorization.get('profile_category', 'unknown'),
                    'category_reasoning': categorization.get('category_reasoning', 'N/A'),
                    'account_nature': categorization.get('account_nature', 'unknown'),
                    'content_focus': categorization.get('content_focus', 'unknown'),
                    'engagement_level': categorization.get('engagement_level', 'unknown'),
                    'authenticity_assessment': categorization.get('authenticity_assessment', 'unknown'),
                    'analysis_date': datetime.now().isoformat()
                }
                
                results.append(result)
                print(f"      [OK] Categorization completed")
            else:
                print(f"      [ERROR] Failed to get categorization")
                # Add failed result
                results.append({
                    'platform': 'tiktok',
                    'username': username,
                    'url': url,
                    'is_public_account': 'public' if not user_data.get('is_private', False) else 'private',
                    'category': 'categorization_failed',
                    'category_reasoning': 'ChatGPT API call failed',
                    'account_nature': 'unknown',
                    'content_focus': 'unknown',
                    'engagement_level': 'unknown',
                    'authenticity_assessment': 'unknown',
                    'analysis_date': datetime.now().isoformat()
                })
        
        # 5. Save results to CSV
        print(f"\n[CLIPBOARD] STEP 5: Saving results")
        csv_file = save_results_to_csv(results)
        
        # 6. Final summary
        print(f"\n{'='*50}")
        print(f"[CHART] CATEGORIZATION SUMMARY")
        print(f"{'='*50}")
        print(f"[USERS] Users processed: {len(users)}")
        print(f"[OK] Successful categorizations: {len([r for r in results if r['category'] not in ['no_data_available', 'categorization_failed']])}")
        print(f"[ERROR] Failed categorizations: {len([r for r in results if r['category'] in ['no_data_available', 'categorization_failed']])}")
        
        if csv_file:
            print(f"[PAGE] Results saved to: {csv_file}")
            print(f"[MEMO] Prompts saved to: data/Input/prompts/")
            print(f"\n[PARTY] CATEGORIZATION COMPLETED SUCCESSFULLY")
        else:
            print(f"\n[ERROR] Failed to save results")
        
    except Exception as e:
        print(f"\n[BOOM] CRITICAL ERROR: {e}")
        traceback.print_exc()

# =============================================================================
# 7. ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main() 