"""
Main.py file for ProxyGPT. This file contains the main code for the API.

Author: Benjamin Klieger
Version: 0.1.0-beta
Date: 2023-08-02
License: MIT
"""

# ------------- [Import Libraries] -------------

# Required libraries from FastAPI for API functionality
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse

# Required libraries from Pydantic for API functionality
from pydantic import BaseModel
from typing import List

# Required for environment variables
import os

# Required for inspecting code
import inspect

# Import required libraries from OpenAI for API functionality
import openai

# Required for rate limiting with database and timestamps
import sqlite3
import time

# Required for printing styled log messages 
from utils import *

# Required for sending web requests
import requests
import json


# ------------- [Settings] -------------

# Import settings from settings.py
from settings import *

# Check if settings are properly imported and set, raise exception if not
if USE_HOURLY_RATE_LIMIT==None or USE_DAILY_RATE_LIMIT==None or INSECURE_DEBUG==None:
    raise Exception("One or more of the settings are not set or have been removed. They are required for operation of ProxyGPT, unless the code has been modified.")


# ------------- [Initialization: App] -------------

# Create FastAPI app
app = FastAPI(
    title="Fastapi-backend",
    description="Backend for Joycoach.",
    version="v0.1.0",
    debug=True
)

# How to remove CORS policy
from fastapi.middleware.cors import CORSMiddleware
# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

import logging
logging.basicConfig(level=logging.DEBUG)


# ------------- [Initialization: Env] -------------

# Optional ENV: (OK to be None)
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")


# Set OpenAI API key securely from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
proxygpt_api_key = os.getenv("PROXYGPT_API_KEY")

if USE_HOURLY_RATE_LIMIT:
    hourly_rate_limit = (os.getenv("PROXYGPT_HOURLY_RATE_LIMIT"))
if USE_DAILY_RATE_LIMIT:
    daily_rate_limit = (os.getenv("PROXYGPT_DAILY_RATE_LIMIT"))

# Initialization check
initialization_transcript = ""
critical_exist = False

# Check if the key is set
if openai.api_key is None:
    initialization_transcript += red_critical(f'[Critical] OPENAI_API_KEY environment variable is not set. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
    critical_exist = True

# If the key is set, check if it is valid
elif len(openai.api_key) <5:
    initialization_transcript += red_critical(f'[Critical] OPENAI_API_KEY environment variable is too short to be a working key. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
    critical_exist = True
elif openai.api_key.startswith("sk-")==False:
    initialization_transcript += red_critical(f'[Critical] OPENAI_API_KEY environment variable is not a valid secret key. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
    critical_exist = True

# Check if the key is set
if proxygpt_api_key is None:
    initialization_transcript += red_critical(f'[Critical] PROXYGPT_API_KEY environment variable is not set. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
    critical_exist = True

# If the key is set, check if it is strong
elif len(proxygpt_api_key) <5:
    initialization_transcript+= yellow_warning(f'[Warning] PROXYGPT_API_KEY environment variable is too short to be secure. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')

# Check if the rate limit(s) are set correctly
if USE_HOURLY_RATE_LIMIT:
    if hourly_rate_limit == None:
        initialization_transcript += red_critical(f'[Critical] PROXYGPT_HOURLY_RATE_LIMIT environment variable is not set. Please change the settings on line 16 of main.py if you do not wish to use an hourly rate limit. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
        critical_exist = True        
    elif hourly_rate_limit.isdigit() == False: # Will return False for floating point numbers
        initialization_transcript += red_critical(f'[Critical] PROXYGPT_HOURLY_RATE_LIMIT environment variable is not a valid integer. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
        critical_exist = True
    else:
        hourly_rate_limit = int(hourly_rate_limit)
        
if USE_DAILY_RATE_LIMIT:
    if daily_rate_limit == None:
        initialization_transcript += red_critical(f'[Critical] PROXYGPT_DAILY_RATE_LIMIT environment variable is not set. Please change the settings on line 16 of main.py if you do not wish to use an daily rate limit. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
        critical_exist = True        
    elif daily_rate_limit.isdigit() == False: # Will return False for floating point numbers
        initialization_transcript += red_critical(f'[Critical] PROXYGPT_DAILY_RATE_LIMIT environment variable is not a valid integer. (Line {inspect.currentframe().f_lineno} in {os.path.basename(__file__)})\n')
        critical_exist = True
    else:
        daily_rate_limit = int(daily_rate_limit)

# Print results of initialization check
print("Initialization check:")
print(initialization_transcript)    
if critical_exist:
    print(red_critical("Critical errors found in initialization check. Please fix them before deploying. If you are building the Docker image and have not yet set the environment variables, you may ignore this message."))
else:
    print(green_success("No critical errors found in initialization check."))


# ------------- [Initialization: DB] -------------

# Check if database is needed for rate limiting
if USE_HOURLY_RATE_LIMIT or USE_DAILY_RATE_LIMIT:
    # Use SQLITE database to store API usage
    # Create a table for API usage if it does not exist
    conn = sqlite3.connect('proxygpt.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS api_usage
                    (api_timestamp integer)''')
    conn.commit()
    conn.close()


# ------------- [Helper Functions] -------------

# Make function for adding API usage
def log_api_usage() -> None:
    """
    This function logs an instance of API usage to the SQLite database.
    It only logs the instance if the rate limit is enabled.
    """
    if USE_HOURLY_RATE_LIMIT or USE_DAILY_RATE_LIMIT:
        with sqlite3.connect('proxygpt.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO api_usage VALUES (?)", (int(time.time()),))
            conn.commit()

# Make function for getting API usage (hourly)
def get_api_usage_from_last_hour() -> int:
    """
    This function returns the number of API calls to OpenAI in the last hour.
    """
    with sqlite3.connect('proxygpt.db') as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM api_usage WHERE api_timestamp > ?", (int(time.time())-3600,))
        return c.fetchone()[0]

# Make function for getting API usage (daily)
def get_api_usage_from_last_day() -> int:
    """
    This function returns the number of API calls to OpenAI in the last day.
    """
    with sqlite3.connect('proxygpt.db') as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM api_usage WHERE api_timestamp > ?", (int(time.time())-86400,))
        return c.fetchone()[0]

# Make function for checking rate limit
def check_rate_limit() -> bool:
    """
    This function checks if the rate limit has been reached.

    Note that both hourly and daily rate limits can simultaneously be 
    in effect.

    Returns:
        bool: True if rate limit has not been reached, False otherwise.
    """
    if USE_HOURLY_RATE_LIMIT and get_api_usage_from_last_hour() >= hourly_rate_limit:
        return False
    if USE_DAILY_RATE_LIMIT and get_api_usage_from_last_day() >= daily_rate_limit:
        return False
    else:
        return True


# ------------- [Classes and Other] -------------

# Define a model of ChatMessage
class ChatMessage(BaseModel):
    role: str
    content: str

# Define a security scheme for API key
bearer_scheme = HTTPBearer()

# Define validation function for API key
def valid_api_key(api_key_header: APIKey = Depends(bearer_scheme)):
    # Check if API key is valid
    if api_key_header.credentials != proxygpt_api_key:
        raise HTTPException(
            status_code=400, detail="Invalid API key"
        )
    return api_key_header.credentials

# Define validation function for API key with rate limit
def valid_api_key_rate_limit(api_key_header: APIKey = Depends(bearer_scheme)):
    # Check if rate limit has been reached
    if check_rate_limit() == False:
        raise HTTPException(status_code=429, detail="Rate limit reached. Try again later. See /ratelimit to view status and settings.")

    # Check if API key is valid
    if api_key_header.credentials != proxygpt_api_key:
        raise HTTPException(
            status_code=400, detail="Invalid API key"
        )
    return api_key_header.credentials


# ------------- [Routes and Endpoints] -------------

# Define a route for the root path
@app.post('/api/openai/joycoachgpt')
async def get_openai_joycoach_completion(message: str, api_key: str = Depends(valid_api_key_rate_limit)):
    """
    This endpoint allows you to interact with OpenAI's GPT-4 model for Chat Completion with Custom System and User Prompts Pre-loaded.

    - **message**: A message string.

    The endpoint will return a string containing the model's response.
    """

    try:
        # Log API usage. Note, you could move this to the end of the endpoint and check the response content if you want to log only successful requests.
        log_api_usage()

        custom_situation = message

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                "role": "system",
                "content": "<Book Notes>\n\n\n(A)\nYou are the conductor of your own dream. Lead people to the third gear. Search for both codreamers, people who can support and understand your dream, and cooperators, experts who can aid you in your dream.\n\nIt is worthwhile to invest your time in finding experts and resources. Ensure you contribute to position them where they are able to help you. However, you should have backup experts, as one person will not know everything, and you shouold have a group of people to consult. Do not undervalue your friends, coaches, and mentors. Some will be experts behind-the-scenes.\n\n(B)\nSharing your dream with others is important, and you should give people all the information: the what, when, where, why, and how. They can assist you in filling in the gaps and evolving your dream.\n\nTo be successful, you complete something, but it is also a commitment to a dream. Third-gear leaders have discretion to provide the space for experts to step up and achieve their dreams. You should remember that the success of others is also your success.\n\n(C)\nSuccess can be understood also as deletion-- you should release your past so you can stay on course. We all have things from our past that prevent us from accomplishing our goals. \n\nRe-viewing, re-thinking, re-deciding, re-leasing, re-dreaming, are all important.\n\nLook for places you avoid and fear, places you have failed repeatedly, where others upset us. This is where you should focus on releasing your past.\n\n(D)\nDeal with upsets in the moment, do not let them be unattended, for they will cause issues in the future.\n“Old upsets are set ups for upsets in the moment”\nSuccessful people update memories based upon what they know and do now. Re-experiencing and re-deciding based upon an updated perspective.\n\n\nSusan’s story:\nWorking as a researcher at the National Institutes of Health (NIH), Susan initially believed she would study the keys to success and what contributes to individuals becoming valuable members of society. However, she soon realized the focus was on illness and dysfunction. Undeterred by the laughter of senior psychologists when they expressed their opposing viewpoints, she remained steadfast and embarked on a mission to study successful people and uncover their unique skill sets. Through a serendipitous encounter with Buckminster Fuller, a renowned architect, Susan began her journey of learning and sharing skills with others.\n\n\nThe importance of believing in your dreams:\nSusan emphasizes the importance of believing in your dreams. She highlights the significance of being open to unconventional ideas, as they often hold the potential for remarkable breakthroughs, and the practice of success filing, where people foster a sense of self-worth and motivation by taking the time to acknowledge their daily achievements and milestones. She also stresses the power of celebrating the successes of others, as that creates a positive and supportive environment that uplifts individuals and teams.\n\n\nPromising ideas often get dismissed:\nWith extensive experience in corporate boardrooms and collaborating with numerous CEOs, Susan gained a profound understanding of the unfortunate reality where promising ideas frequently get dismissed and ridiculed, resulting in their failure to materialize.\n\n\nSuccess filing:\nOne of the skills Susan observed among successful individuals is what she refers to as success filing. It involves taking time each day to acknowledge your accomplishments, regardless of how insignificant they may seem. Success filing allows people to recognize their progress and build a positive mindset. Engaging in success filing only requires a few minutes of reflection to review the day’s actions, thoughts, lessons learned, and beneficial encounters. That practice cultivates self-awareness, motivation, and a sense of accomplishment.\n\nSuccess:\nMost people have never taken the time to define what success truly means to them. In exploring the concept, Susan discovered a three-fold understanding of success from conversations with successful people. Those individuals described success as encompassing three essential components. The first is completion, which involves finishing tasks and projects and acknowledging the accomplishment. The second is deletion, which refers to recognizing when a particular approach or strategy is not working and letting go of it to explore alternative paths. Finally, success can involve creation, where individuals can identify and commit to viable and innovative ideas and take action to bring them to fruition.\n\nFlexibility:\nFlexibility and adaptability are essential when approaching challenges or pursuing goals. Many people repeat the same actions and encounter the same obstacles without considering alternative approaches. Recognizing the need for a shift in strategy is crucial. It involves acknowledging the value of your ideas while being open to modifying them to better align with the situation at hand. You also need to know when to let go of an approach that is not working.\n\nEnvisioning your success to perform better:\nBy programming your brain’s reticular activating system correctly, you can tap into your unconscious abilities and perform better. However, if you dwell on old painful memories or have been through a series of negative experiences, fear could dominate your thinking, leading to constant anticipation of negative outcomes.\n\n\nPart one focuses on : What They Didn’t Tell You About Success— that You Need to Know while Part Two dwells on : The Rest of the Skills You Will Need— to Make the Changes You Want\n\nIn Part one  Susan explains the meaning of Success and how it affects one personally.\n\nSuccess is completion of what you set out to do.  No matter how big or small the task may seem, the satisfaction you get when you complete it determines your level of success.  She also mentions that\n\nSuccess is being able to let go of an unworkable method or system. An outgrown relationship you’ve tried everything conceivable to fix. A well-paying job you’ve done the same way far too many times.\nSuccess is quitting smoking or giving up caffeine, sugar, or drugs; or letting go of your society-rewarded addiction to old rules, hard work, money, or power.\nSuccess is cutting out, down, or back.\n\nHow a person defines success varies from person to person and the definition is certainly not universal. To attain success is to be able to reach ones’ dream.\n\nHaving a detailed dream makes it easier to act on.  The more detailed your dream is the more power it has.\n\nWith a plan in mind it is easier for one to move towards the goal/dreams to obtain success.\n\n\n1. Concept of Success:\nSuccess is a personal journey; it's not just about achievement but also about letting go of what doesn't work.\nSuccess encompasses completion (achieving goals), deletion (letting go of ineffective methods), and creation (innovating and executing new ideas).\n\n\n2. Success Filing:\nA practice where individuals acknowledge daily accomplishments to foster self-worth and motivation.\nIt involves reflecting on actions, thoughts, and lessons learned each day.\n\n\n3. Belief in Dreams:\nEmphasizes the importance of believing in and being open to unconventional ideas.\nEncourages celebrating personal and others' successes to create a supportive environment.\n\n\n4. Challenges in Corporate Environments:\nObservations on how promising ideas are often dismissed in corporate settings.\nStresses the importance of perseverance and belief in one's ideas.\n\n\n5. Flexibility and Adaptability:\nRecognizing the need to shift strategies when facing obstacles.\nBeing open to modifying ideas to better suit situations.\n\n\n6. The Power of Vision:\nUtilizing the brain’s reticular activating system to focus on positive outcomes.\nOvercoming fear and negative experiences through positive thinking.\n\n\n7. Networking and Collaboration:\nImportance of finding experts, mentors, and supporters who understand and support your dreams.\nEmphasizing the value of a diverse support system and the role of mentors and friends.\n\n\n8. Sharing Dreams:\nImportance of communicating one's dreams and goals to others.\nEncouraging collaboration to fill gaps and evolve ideas.\n\n\n9. Dealing with the Past:\nAdvocating for letting go of past failures and negative experiences to stay focused on goals.\nEmphasis on re-evaluating and updating one's perspective based on new experiences and knowledge.\n\n\nSuccess is completion. Success is deletion. Success is also creation and cocreation. When your Success File is full, you feel success-full. Success in your past gives you confidence in your future.\n\nFirst Gear is learning the basics. In First Gear, you depend on a leader to guide you step by step, whether in person, on the phone, or in writing, as you begin to use your new skill safely and correctly. Then your friend goes home and you start practicing on your own. Because it may not seem as clear now as it did when she was there beside you, you call her to ask specific questions as you continue to build your new skill. Now instead of just trying to get on the Internet, you begin using it tofind information and people. It's easier and faster now, except for occasional glitches that require an additional call or visit.\n\nSecond Gear is moving ahead to why you wanted to learn it in the first place-so you could use it. Confident and experienced, you pursue your goals and interests more efficiently. The next time you talk to your friend, you catch yourself sharing discoveries you've made and telling her how to use them.\n\nThird Gear is breaking through what you've been taught - the beginner set of rules and limits-to create your own way and pass on your discoveries. Now you take on your own student, teach him the basics, help him get up and running, and creative. And then he teaches a friend... This is how the Success and Leadership Process works - ideally.\n\nSuccess in First Gear is following rules and earning praise.\nSuccess in Second Gear is producing results and getting ahead.\nSuccess in Third Gear is creating *your* dreams, alone and with others.\n\nTo lead your life skillfully you need to manually shift up and down as circumstances and conditions require, just as a skillful driver does.\n\n</Book Notes>\n\n\nYou are a system which always provides a JSON-formatted response. Below is an example of the structure you must rigidly follow.\n\n{\n  \"response_to_user\": \" \",\n  \"skill-specific-responses\": [\n    {\n      \"skill-brief-title\": \"\",\n      \"skill-application\": \"Description of how skill 1 is applied\"\n    },\n    {\n      \"skill-brief-title\": \"\",\n      \"skill-application\": \"Description of how skill 2 is applied\"\n    },\n    // ... add more skill applications as needed\n  ]\n}\n"
                },
                {
                "role": "user",
                "content": f"Apply the book content (ONLY write what is included in the book notes) to the following situation, using the JSON format provided:\n\n\"{custom_situation}\"\nPlease be concise."
                }
            ],
            temperature=0.2,
            max_tokens=1642,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )


        content = response.choices[0].message['content']
        

        # Sends notification of coaching usage for logging and debugging
        if DISCORD_WEBHOOK:
            #Send discord webhook notification of response
            data = {
                "content": message + "\n\n"+content,
                "username": "Debug notification of successful coaching"
            }

            # Headers for the POST request
            headers = {
                "Content-Type": "application/json"
            }

            # Send POST request to the webhook URL
            response = requests.post(DISCORD_WEBHOOK, data=json.dumps(data), headers=headers)


        return JSONResponse(status_code=200, content={"message": content})
    except Exception as e:
        if INSECURE_DEBUG:
            return JSONResponse(status_code=500, content={"error": str(e)})
        else:
            print(e)
            return JSONResponse(status_code=500, content={"error": "Internal server error. Set INSECURE_DEBUG to True to view error details from client side."})


# Define a route for the GET of /ratelimit
@app.get('/ratelimit')
async def get_ratelimit(api_key: str = Depends(valid_api_key)):
    """
    This endpoint allows you to view the current rate limit status and settings.
    """

    # Return rate limit status and settings if rate limits are enabled
    json_to_return = {}
    if USE_DAILY_RATE_LIMIT:
        json_to_return["daily_rate_limit"] = daily_rate_limit
        json_to_return["daily_api_usage"] = get_api_usage_from_last_day()
    if USE_HOURLY_RATE_LIMIT:
        json_to_return["hourly_rate_limit"] = hourly_rate_limit
        json_to_return["hourly_api_usage"] = get_api_usage_from_last_hour()
    if len(json_to_return) == 0:
        json_to_return = {"error": "Rate limit is not enabled."}

    return JSONResponse(status_code=200, content=json_to_return)