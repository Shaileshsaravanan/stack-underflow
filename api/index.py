from flask import Flask, request, render_template, jsonify
import google.generativeai as genai
import requests
from environs import Env
from collections import Counter

GITHUB_API_URL = "https://api.github.com/users/{username}"
GITHUB_REPOS_URL = "https://api.github.com/users/{username}/repos"

import re

def clean_text(text):
    text = re.sub(r'\\[nrt"]', ' ', text)
    text = text.replace("\u2019", "'")
    text = text.replace("`", "")
    text = text.replace("\\/", "/")
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace("\n", " ")

brainrot = """
GYATTT – Expression of excitement or admiration (often ironic and use more Ts for emphasis),  
ONG / OMM – "On God" / "On My Momma" (swearing truth),  
FR / FRFR – "For real" / "For real, for real" (emphasizing honesty),  
NO CAP – "Not lying" or "seriously,"  
BET – Agreement or challenge (e.g., "Alright, bet"),  
W / L – Win / Loss (used to rate things),  
RIZZ – Charisma or flirting skills,  
GRIMACE SHAKE ERA – Absurd chaos reference,  
YEET – Throwing something or expressing excitement,  
GOOBER / SCRIMBLO / BLORB – Silly or dumb person,  
JIT – Kid or young person,  
MFS IN SHAMBLES – People are upset (often sarcastic),  
IT’S GIVING – Describes a vibe (e.g., "It’s giving main character"),  
BFFR – "Be for real" (calling out nonsense),  
MID – Mediocre or underwhelming,  
SUS – Suspicious or questionable,  
DEADASS – Completely serious,  
BRUH – Expression of disappointment or disbelief,  
SKIBIDI – Random internet meme nonsense,  
HE COOKED / LET HIM COOK – Someone is doing something well (or about to),  
WE BALL – Keep going despite setbacks,  
BOOFED – Consumed (often substances) in a dumb way,  
BASED – Confident or unapologetic in an opinion,  
MALDING – Mad + Balding (used to mock angry people),  
LOWKEY / HIGHKEY – Somewhat / Very much,  
COPE / SEETHE / DILATE – Insult for someone upset about something,  
L+RATIO – Mocking someone for an "L" (loss),  
PACKWATCH – Celebrating someone's downfall,  
GOBLIN MODE – Acting feral or unhinged,  
CHONK – Lovable, fat, and round (often for animals)."""

brainrot_prompt = f"""YO AI, I need you to go FULL BRAINROT MODE. I’m talkin’ **GYATTTT** levels of unhinged. None of that soft, watered-down corporate goober talk—**I WANT MAXIMUM CHAOS**. 

Spam W/L, RIZZ, GYATTT, ong frfr, LET HIM COOK, and just **absolutely obliterate clarity**. Make it feel like an **overcaffeinated Zoomer gremlin** is rambling at the speed of light. **Tone should be deranged, borderline incoherent, but still readable**. 

**EXAMPLES OF THE VIBE I WANT:**  
- “GYATTTT my neurons just short-circuited ong this built diffy”  
- “Bro cooked so hard the kitchen exploded, no cap”  
- “This some next-level goblin mode, jit went from mid to W in 0.2s”  
- “Packwatch 💀💀 ratio + didn’t ask + skill issue”  

KEEP IT UNHINGED, KEEP IT FAST-PACED, KEEP IT **BRAINROT.** **FULL DISASSOCIATION ENERGY.** GO WILD. some brainrot terms - {brainrot}"""

def get_github_user_details(username):
    user_data = requests.get(GITHUB_API_URL.format(username=username)).json()
    
    if "message" in user_data and user_data["message"] == "Not Found":
        return {"Error": "User not found"}
    
    repos_data = requests.get(GITHUB_REPOS_URL.format(username=username)).json()
    print(repos_data)
    
    languages = Counter()
    repo_details = []
    
    for repo in repos_data:
        print(repo)
        repo_details.append({
            "Repo Name": repo["name"],
            "Description": repo["description"],
            "Stars": repo["stargazers_count"],
            "Forks": repo["forks_count"],
            "Language": repo["language"],
            "Repo URL": repo["html_url"]
        })
        if repo["language"]:
            languages[repo["language"]] += 1

    full_profile = {
        "Username": user_data.get("login"),
        "Name": user_data.get("name"),
        "Bio": user_data.get("bio"),
        "Location": user_data.get("location"),
        "Company": user_data.get("company"),
        "Blog": user_data.get("blog"),
        "Profile URL": user_data.get("html_url"),
        "Avatar URL": user_data.get("avatar_url"),
        "Public Repos": user_data.get("public_repos"),
        "Followers": user_data.get("followers"),
        "Following": user_data.get("following"),
        "Languages Used": dict(languages),
        "Repositories": repo_details
    }
    
    return full_profile

env = Env()
env.read_env()
apikey = env.str('apikey')
genai.configure(api_key=apikey)

app = Flask(__name__)

def get_gemini_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text if response else "Something went wrong, try again."

@app.route('/api/why', methods=['POST'])
def why():
    problem = request.json['problem']

    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""The user has reported that {problem}. 
    Generate a completely ridiculous, funny, and absurd reason why this might be happening. 
    Be creative, and make sure the response is entertaining but still sounds somewhat technical, 
    keep it short under a sentence. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/github')
def github():
    username = request.args.get('username')
    if not username:
        return jsonify({"Error": "Please provide a username"})
    
    brainrot_stuff = ""

    if request.args.get('brainrot'):
        brainrot_stuff = brainrot_prompt
    
    try:
        user_data = get_github_user_details(username)
        prompt = f""" Absolutely roast this GitHub profile: {user_data}. 
        Make it **funny, sarcastic, and absurd**—not constructive, not motivational, just straight-up **brutal comedy**.
        Think of it like a tech roast at a stand-up show. No introductions, no "alright folks", just **straight into the jokes**. 
        Make fun of repo names, star count, random programming languages—go wild but keep it **fun and not offensive**.
        Be witty, be sharp, be creative. **No sugarcoating.** No boring analysis. **Max humor, max chaos.**
        {brainrot_stuff}
        """
        
        response = get_gemini_response(prompt)
        return jsonify(clean_text(response))
    
    except Exception as e:
        return jsonify("GitHub API rate limit exceeded, try again later.")

@app.route('/api/feature')
def feature():
    brainrot_stuff = ""

    if request.args.get('brainrot'):
        brainrot_stuff = brainrot_prompt
    
    response = get_gemini_response(f"""Invent a completely unnecessary AI-powered 
    feature. Make it sound high-tech but utterly useless. keep it short and ridiculous. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/motivation')
def motivation():
    brainrot_stuff = ""

    if request.args.get('brainrot'):
        brainrot_stuff = brainrot_prompt
    
    response = get_gemini_response(f"""Generate an exaggerated startup-style motivational 
    quote using words like 'disrupt,' 'scale,' and 'AI'. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/explain')
def explain():
    term = request.args.get('term')

    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""Explain the concept of '{term}' in a way that a 
    grandma would understand. Use funny, everyday analogies. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/excuse', methods=['POST'])
def excuse():
    reason = request.json.get("reason")

    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""Give a wild and absurd excuse for missing {reason}. Make it sound 
    completely ridiculous yet somehow plausible. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/startup', methods=['GET'])
def startup():
    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""Invent a startup idea that makes no sense but sounds like the future. 
    Use exaggerated tech jargon. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/roast', methods=['POST'])
def roast():
    tech_stack = request.json.get("tech_stack")

    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""Roast a developer who uses {tech_stack}. Be funny but harsh. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/bad_advice', methods=['GET'])
def bad_advice():
    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""Give a programming tip that is completely useless but sounds like expert advice. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/fortune', methods=['GET'])
def fortune():
    brainrot_stuff = ""

    if request.args.get('brainrot') == "true":
        brainrot_stuff = brainrot_prompt

    response = get_gemini_response(f"""Give me a fortune cookie message that sounds wise but makes no sense. {brainrot_stuff}""")
    return jsonify(clean_text(response))

@app.route('/api/brainrot', methods=['POST'])
def brainrot():
    prompt = request.json.get("prompt")
    response = get_gemini_response(prompt + brainrot_prompt)

    return jsonify(clean_text(response))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000)

